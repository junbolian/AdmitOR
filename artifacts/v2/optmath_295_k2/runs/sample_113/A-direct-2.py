import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    profit = params["profit"]
    resource_usage = params["resource_usage"]
    capacity = params["capacity"]
    resource_budget = params["resource_budget"]

    n = len(profit)
    items = list(range(n))

    model = pyo.ConcreteModel()

    model.x = pyo.Var(items, domain=pyo.NonNegativeReals)

    model.profit_expr = pyo.Objective(
        expr=sum(profit[i] * model.x[i] for i in items),
        sense=pyo.maximize,
    )

    model.resource_limit = pyo.Constraint(
        expr=sum(resource_usage[i] * model.x[i] for i in items) <= resource_budget
    )

    model.cap = pyo.Constraint(
        items, rule=lambda model, i: model.x[i] <= capacity[i]
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.profit_expr))
    return {"objective": obj_val, "status": "optimal"}