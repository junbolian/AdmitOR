# IR: {"sets":{"C":[0,1,2,3,4],"M":[0,1,2,3],"P":[0,1]},"params":{"profit":{"indices":["C","M","P"],"source":"params['profit'][c][j][k]","type":"real"},"demand":{"indices":["M","P"],"source":"params['demand'][j][k]","type":"real"}},"variables":{"supply":{"indices":["C","M","P"],"type":"nonnegative_continuous"}},"constraints":["For each (j,k) in M x P: sum(supply[c,j,k] for c in C) == demand[j,k]"],"objective":"maximize sum(profit[c,j,k] * supply[c,j,k] for (c,j,k) in C x M x P)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    profit = params["profit"]
    demand = params["demand"]

    model = pyo.ConcreteModel()

    model.companies = pyo.RangeSet(0, 4)
    model.markets = pyo.RangeSet(0, 3)
    model.products = pyo.RangeSet(0, 1)

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

    def demand_rule(mdl, j, k):
        return (
            sum(mdl.supply[c, j, k] for c in mdl.companies)
            == mdl.required_demand[j, k]
        )

    model.demand_balance = pyo.Constraint(
        model.markets,
        model.products,
        rule=demand_rule,
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
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_profit))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}