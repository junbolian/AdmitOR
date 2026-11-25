# IR: {"sets":{"companies":[0,1,2,3],"markets":[0,1,2,3,4],"products":[0,1]},"params":{"demand":{"indices":["markets","products"],"type":"real","source":"params['demand']"},"profit":{"indices":["companies","markets","products"],"type":"real","source":"params['profit']"}},"variables":{"supply":{"indices":["companies","markets","products"],"type":"nonnegative continuous"}},"constraints":["For each market j and product k: sum(supply[i,j,k] for i in companies) == demand[j,k]"],"objective":{"sense":"maximize","expression":"sum(profit[i,j,k] * supply[i,j,k] for i in companies for j in markets for k in products)"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    demand = params["demand"]
    profit = params["profit"]

    model = pyo.ConcreteModel()
    model.companies = pyo.RangeSet(0, 3)
    model.markets = pyo.RangeSet(0, 4)
    model.products = pyo.RangeSet(0, 1)

    model.demand = pyo.Param(
        model.markets,
        model.products,
        initialize=lambda mdl, j, k: demand[j][k],
        within=pyo.Reals,
    )
    model.profit = pyo.Param(
        model.companies,
        model.markets,
        model.products,
        initialize=lambda mdl, i, j, k: profit[i][j][k],
        within=pyo.Reals,
    )

    model.supply = pyo.Var(
        model.companies,
        model.markets,
        model.products,
        domain=pyo.NonNegativeReals,
    )

    def demand_balance_rule(mdl, j, k):
        return (
            sum(mdl.supply[i, j, k] for i in mdl.companies)
            == mdl.demand[j, k]
        )

    model.demand_balance = pyo.Constraint(
        model.markets,
        model.products,
        rule=demand_balance_rule,
    )

    model.total_profit = pyo.Objective(
        expr=sum(
            model.profit[i, j, k] * model.supply[i, j, k]
            for i in model.companies
            for j in model.markets
            for k in model.products
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPsi raises this when it cannot load a feasible solution.
        if "a feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_profit))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}