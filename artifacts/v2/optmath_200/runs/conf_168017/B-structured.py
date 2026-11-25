# IR: {"sets":{"C":[0,1,2,3],"P":[0,1],"M":[0,1,2]},"params":{"demand[p,k]":"params['demand_p{p}_m{k}']","profit[c,p,k]":"params['profit_c{c}_p{p}_m{k}']"},"variables":{"supply[c,p,k]":"NonNegativeReals"},"constraints":["sum(c in C, supply[c,p,k]) == demand[p,k] for each p in P, k in M"],"objective":"maximize sum(c in C, p in P, k in M, profit[c,p,k]*supply[c,p,k])"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.C = pyo.Set(initialize=[0, 1, 2, 3], ordered=True)
    model.P = pyo.Set(initialize=[0, 1], ordered=True)
    model.M = pyo.Set(initialize=[0, 1, 2], ordered=True)

    model.demand = pyo.Param(
        model.P,
        model.M,
        initialize={
            (p, k): params[f"demand_p{p}_m{k}"]
            for p in model.P
            for k in model.M
        },
        within=pyo.Reals,
    )
    model.profit = pyo.Param(
        model.C,
        model.P,
        model.M,
        initialize={
            (c, p, k): params[f"profit_c{c}_p{p}_m{k}"]
            for c in model.C
            for p in model.P
            for k in model.M
        },
        within=pyo.Reals,
    )

    model.supply = pyo.Var(
        model.C, model.P, model.M, domain=pyo.NonNegativeReals
    )

    def demand_rule(instance, p, k):
        return (
            sum(instance.supply[c, p, k] for c in instance.C)
            == instance.demand[p, k]
        )

    model.demand_balance = pyo.Constraint(
        model.P, model.M, rule=demand_rule
    )

    model.total_profit = pyo.Objective(
        expr=sum(
            model.profit[c, p, k] * model.supply[c, p, k]
            for c in model.C
            for p in model.P
            for k in model.M
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