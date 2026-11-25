import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    profit_margin = params["profit_margin"]
    resource_consumption = params["resource_consumption"]
    resource_capacity = params["resource_capacity"]
    production_limit = params["production_limit"]

    n = len(profit_margin)
    items = list(range(n))

    model = pyo.ConcreteModel()
    model.x = pyo.Var(items, within=pyo.NonNegativeReals)

    model.resource_constraint = pyo.Constraint(
        expr=sum(resource_consumption[i] * model.x[i] for i in items)
        <= resource_capacity
    )

    model.limit_constraint = pyo.Constraint(
        items,
        rule=lambda m, i: m.x[i] <= production_limit[i],
    )

    model.obj = pyo.Objective(
        expr=sum(profit_margin[i] * model.x[i] for i in items),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.obj))
    except Exception as err:
        return {"objective": None, "status": "solver failed: " + type(err).__name__}

    return {"objective": obj_val, "status": "optimal"}