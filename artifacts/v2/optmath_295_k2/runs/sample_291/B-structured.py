# IR: {"sets":{"companies":[0,1,2,3,4],"markets":[0,1]},"params":{"profit":"real[companies,markets]","demand":"real[markets]"},"variables":{"supply":"nonnegative continuous[companies,markets]"},"constraints":["For each market j: sum(supply[i,j] for i in companies) == demand[j]"],"objective":"maximize sum(profit[i,j] * supply[i,j] for i in companies for j in markets)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.companies = pyo.RangeSet(0, 4)
    model.markets = pyo.RangeSet(0, 1)

    model.profit = pyo.Param(
        model.companies,
        model.markets,
        initialize={
            (i, j): params["profit"][i][j]
            for i in model.companies
            for j in model.markets
        },
        within=pyo.Reals,
    )
    model.demand = pyo.Param(
        model.markets,
        initialize={j: params["demand"][j] for j in model.markets},
        within=pyo.Reals,
    )

    model.supply = pyo.Var(
        model.companies,
        model.markets,
        domain=pyo.NonNegativeReals,
    )

    def demand_rule(instance, j):
        return (
            sum(instance.supply[i, j] for i in instance.companies)
            == instance.demand[j]
        )

    model.demand_satisfaction = pyo.Constraint(
        model.markets, rule=demand_rule
    )

    model.total_profit = pyo.Objective(
        expr=sum(
            model.profit[i, j] * model.supply[i, j]
            for i in model.companies
            for j in model.markets
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