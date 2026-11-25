import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    capacity = params["capacity"]
    values = params["values"]
    weights = params["weights"]
    n = len(values)

    model = pyo.ConcreteModel()
    model.x = pyo.Var(range(n), domain=pyo.Binary)

    model.obj = pyo.Objective(
        expr=sum(values[i] * model.x[i] for i in range(n)),
        sense=pyo.maximize,
    )

    model.weight_con = pyo.Constraint(
        expr=sum(weights[i] * model.x[i] for i in range(n)) <= capacity
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}