import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    profit = params["profit"]
    resource_rate = params["resource_rate"]
    resource_capacity = params["resource_capacity"]
    production_limit = params["production_limit"]

    n = len(profit)

    model = pyo.ConcreteModel()
    model.Items = pyo.RangeSet(0, n - 1)

    model.x = pyo.Var(model.Items, domain=pyo.NonNegativeReals,
                      bounds=lambda m, i: (0, production_limit[i]))

    model.resource_constraint = pyo.Constraint(
        expr=sum(resource_rate[i] * model.x[i] for i in model.Items)
        <= resource_capacity
    )

    model.obj = pyo.Objective(
        expr=sum(profit[i] * model.x[i] for i in model.Items),
        sense=pyo.maximize
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))

    return {"objective": obj_val, "status": "optimal"}