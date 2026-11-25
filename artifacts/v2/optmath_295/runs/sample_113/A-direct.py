import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    profit_margin = params["profit_margin"]
    resource_usage = params["resource_usage"]
    capacity = params["capacity"]
    resource_limit = params["resource_limit"]

    n = len(profit_margin)
    items = range(n)

    model = pyo.ConcreteModel()
    model.x = pyo.Var(items, within=pyo.NonNegativeReals, bounds=lambda m, i: (0, capacity[i]))

    model.profit = pyo.Objective(
        expr=sum(profit_margin[i] * model.x[i] for i in items),
        sense=pyo.maximize,
    )

    model.resource = pyo.Constraint(
        expr=sum(resource_usage[i] * model.x[i] for i in items) <= resource_limit
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.profit))
    return {"objective": obj_val, "status": "optimal"}