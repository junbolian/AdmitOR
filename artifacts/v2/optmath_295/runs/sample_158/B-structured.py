# IR: {"sets":{"C":[0,1,2],"M":[0,1,2,3],"P":[0,1]},"params":{"profit[c,j,k]":"params['profit'][c][j][k], real","demand[j,k]":"params['demand'][j][k], real"},"variables":{"x[c,j,k]":"nonnegative real"},"constraints":["sum(x[c,j,k] for c in C) == demand[j,k] for j in M, k in P"],"objective":"maximize sum(profit[c,j,k]*x[c,j,k] for c in C, j in M, k in P)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.C = pyo.Set(initialize=range(3), ordered=True)
    model.M = pyo.Set(initialize=range(4), ordered=True)
    model.P = pyo.Set(initialize=range(2), ordered=True)

    model.profit = pyo.Param(
        model.C,
        model.M,
        model.P,
        initialize={
            (company, market, product): params["profit"][company][market][product]
            for company in model.C
            for market in model.M
            for product in model.P
        },
        within=pyo.Reals,
    )

    model.demand = pyo.Param(
        model.M,
        model.P,
        initialize={
            (market, product): params["demand"][market][product]
            for market in model.M
            for product in model.P
        },
        within=pyo.Reals,
    )

    model.x = pyo.Var(
        model.C, model.M, model.P, domain=pyo.NonNegativeReals
    )

    def demand_rule(mdl, market, product):
        return (
            sum(mdl.x[company, market, product] for company in mdl.C)
            == mdl.demand[market, product]
        )

    model.demand_satisfaction = pyo.Constraint(
        model.M, model.P, rule=demand_rule
    )

    model.total_profit = pyo.Objective(
        expr=sum(
            model.profit[company, market, product]
            * model.x[company, market, product]
            for company in model.C
            for market in model.M
            for product in model.P
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