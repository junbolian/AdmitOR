# IR: {"sets":{"C":[0,1,2,3,4],"M":[0,1,2,3],"P":[0,1]},"params":{"profit":{"indices":["C","M","P"],"source":"params['profit'][c][j][k]","type":"real"},"demand":{"indices":["M","P"],"source":"params['demand'][j][k]","type":"real"}},"variables":{"supply":{"indices":["C","M","P"],"type":"nonnegative_continuous"}},"constraints":["For each j in M and k in P: sum(supply[c,j,k] for c in C) == demand[j,k]"],"objective":{"sense":"maximize","expression":"sum(profit[c,j,k]*supply[c,j,k] for c in C for j in M for k in P)"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    profit = params["profit"]
    demand = params["demand"]

    model = pyo.ConcreteModel()

    model.companies = pyo.Set(initialize=range(5), ordered=True)
    model.markets = pyo.Set(initialize=range(4), ordered=True)
    model.products = pyo.Set(initialize=range(2), ordered=True)

    model.unit_profit = pyo.Param(
        model.companies,
        model.markets,
        model.products,
        initialize={
            (c, j, k): profit[c][j][k]
            for c in model.companies
            for j in model.markets
            for k in model.products
        },
        within=pyo.Reals,
    )

    model.required_demand = pyo.Param(
        model.markets,
        model.products,
        initialize={
            (j, k): demand[j][k]
            for j in model.markets
            for k in model.products
        },
        within=pyo.Reals,
    )

    model.supply = pyo.Var(
        model.companies,
        model.markets,
        model.products,
        domain=pyo.NonNegativeReals,
    )

    def demand_balance_rule(instance, j, k):
        return (
            sum(instance.supply[c, j, k] for c in instance.companies)
            == instance.required_demand[j, k]
        )

    model.demand_balance = pyo.Constraint(
        model.markets,
        model.products,
        rule=demand_balance_rule,
    )

    model.total_profit = pyo.Objective(
        expr=sum(
            model.unit_profit[c, j, k] * model.supply[c, j, k]
            for c in model.companies
            for j in model.markets
            for k in model.products
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_profit))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}