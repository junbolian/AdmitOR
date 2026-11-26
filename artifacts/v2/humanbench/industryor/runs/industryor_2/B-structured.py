# IR: {"sets":{"P":[0,1,2,3]},"params":{"income":"params['income'][i], i in P; ordered Properties 1-4","cost":"params['cost'][i], i in P; ordered Properties 1-4","budget":"params['budget']"},"variables":{"buy[i]":"binary, i in P"},"constraints":["sum(cost[i]*buy[i] for i in P) <= budget","buy[3] + buy[2] <= 1"],"objective":"maximize sum(income[i]*buy[i] for i in P)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """income and cost are sequences ordered by Properties 1, 2, 3, 4."""
    model = pyo.ConcreteModel()
    model.properties = pyo.Set(initialize=range(4), ordered=True)

    model.annual_income = pyo.Param(
        model.properties,
        initialize={i: params["income"][i] for i in range(4)},
    )
    model.purchase_cost = pyo.Param(
        model.properties,
        initialize={i: params["cost"][i] for i in range(4)},
    )
    model.purchase_budget = pyo.Param(initialize=params["budget"])

    model.buy = pyo.Var(model.properties, domain=pyo.Binary)

    model.budget_limit = pyo.Constraint(
        expr=sum(
            model.purchase_cost[i] * model.buy[i]
            for i in model.properties
        ) <= model.purchase_budget
    )
    model.property_exclusion = pyo.Constraint(
        expr=model.buy[3] + model.buy[2] <= 1
    )

    model.total_income = pyo.Objective(
        expr=sum(
            model.annual_income[i] * model.buy[i]
            for i in model.properties
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_income))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}