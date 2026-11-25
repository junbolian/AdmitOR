import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    values = params["values"]
    weights = params["weights"]
    capacity = params["capacity"]
    n = len(values)

    model = pyo.ConcreteModel()
    item_set = pyo.RangeSet(0, n - 1)
    model.x = pyo.Var(item_set, domain=pyo.Binary)

    model.profit = pyo.Objective(
        expr=sum(values[i] * model.x[i] for i in item_set),
        sense=pyo.maximize,
    )

    model.weight_limit = pyo.Constraint(
        expr=sum(weights[i] * model.x[i] for i in item_set) <= capacity
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.profit))
    return {"objective": obj_val, "status": "optimal"}