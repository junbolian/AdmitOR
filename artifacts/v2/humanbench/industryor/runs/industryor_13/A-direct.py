import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    demand = params["demand"]
    n = len(demand)

    model = pyo.ConcreteModel()

    # x[j]: number of salespersons starting their 8-hour shift at period j
    model.x = pyo.Var(range(n), domain=pyo.NonNegativeReals)

    model.obj = pyo.Objective(expr=sum(model.x[j] for j in range(n)), sense=pyo.minimize)

    # Each shift covers 2 consecutive 4-hour periods (8 hours)
    def cover_rule(model, i):
        return model.x[i] + model.x[(i - 1) % n] >= demand[i]

    model.cover = pyo.Constraint(range(n), rule=cover_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}