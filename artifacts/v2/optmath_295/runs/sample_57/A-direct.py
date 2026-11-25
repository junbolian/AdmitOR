import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    profit = params["profit"]
    resource_rate = params["resource_rate"]
    resource_capacity = params["resource_capacity"]
    production_limit = params["production_limit"]

    items = list(range(len(profit)))

    model = pyo.ConcreteModel()

    model.x = pyo.Var(items, domain=pyo.NonNegativeReals,
                      bounds=lambda m, i: (0, production_limit[i]))

    model.obj = pyo.Objective(
        expr=sum(profit[i] * model.x[i] for i in items),
        sense=pyo.maximize
    )

    model.resource_con = pyo.Constraint(
        expr=sum(resource_rate[i] * model.x[i] for i in items) <= resource_capacity
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}