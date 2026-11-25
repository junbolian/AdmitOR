import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    capacity = params["capacity"]
    values = params["values"]
    weights = params["weights"]
    n = len(values)

    model = pyo.ConcreteModel()
    model.item_set = pyo.RangeSet(0, n - 1)
    model.x = pyo.Var(model.item_set, domain=pyo.Binary)

    model.profit = pyo.Objective(
        expr=sum(values[i] * model.x[i] for i in model.item_set),
        sense=pyo.maximize,
    )

    model.weight_limit = pyo.Constraint(
        expr=sum(weights[i] * model.x[i] for i in model.item_set) <= capacity
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.profit))
    return {"objective": obj_val, "status": "optimal"}