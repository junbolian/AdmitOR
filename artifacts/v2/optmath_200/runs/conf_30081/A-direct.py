import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    profit = params["profit"]
    resource_consumption = params["resource_consumption"]
    resource_capacity = params["resource_capacity"]
    production_capacity = params["production_capacity"]

    n = len(profit)
    items = range(n)

    model = pyo.ConcreteModel()
    model.x = pyo.Var(items, domain=pyo.NonNegativeReals)

    model.resource_constraint = pyo.Constraint(
        expr=sum(resource_consumption[i] * model.x[i] for i in items)
        <= resource_capacity
    )

    model.capacity_constraints = pyo.Constraint(
        items, rule=lambda m, i: m.x[i] <= production_capacity[i]
    )

    model.objective = pyo.Objective(
        expr=sum(profit[i] * model.x[i] for i in items),
        sense=pyo.maximize,
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.objective))
    return {"objective": obj_val, "status": "optimal"}