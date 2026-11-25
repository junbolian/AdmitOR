import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    profit = params["profit"]
    resource_coefficient = params["resource_coefficient"]
    resource_capacity = params["resource_capacity"]
    production_limit = params["production_limit"]

    items = list(range(len(profit)))

    model = pyo.ConcreteModel()

    model.x = pyo.Var(items, domain=pyo.NonNegativeReals)

    model.profit_expr = pyo.Expression(
        expr=sum(profit[i] * model.x[i] for i in items)
    )

    model.resource_constraint = pyo.Constraint(
        expr=sum(resource_coefficient[i] * model.x[i] for i in items)
        <= resource_capacity
    )

    model.limit_constraint = pyo.Constraint(
        items, rule=lambda m, i: m.x[i] <= production_limit[i]
    )

    model.obj = pyo.Objective(expr=model.profit_expr, sense=pyo.maximize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}