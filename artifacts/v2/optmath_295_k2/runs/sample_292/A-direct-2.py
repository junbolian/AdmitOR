import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    profit = params["profit"]
    resource_coeff = params["resource_coeff"]
    resource_capacity = params["resource_capacity"]
    upper_limit = params["upper_limit"]

    n = len(profit)
    items = range(n)

    model = pyo.ConcreteModel()

    model.x = pyo.Var(items, within=pyo.NonNegativeReals, bounds=lambda m, i: (0, upper_limit[i]))

    model.obj = pyo.Objective(
        expr=sum(profit[i] * model.x[i] for i in items),
        sense=pyo.maximize,
    )

    model.resource = pyo.Constraint(
        expr=sum(resource_coeff[i] * model.x[i] for i in items) <= resource_capacity
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}