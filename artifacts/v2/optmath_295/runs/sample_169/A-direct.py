import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    capacity = params["capacity"]
    values = params["values"]
    weights = params["weights"]
    n = len(values)

    model = pyo.ConcreteModel()
    model.crops = pyo.Set(initialize=range(n))
    model.x = pyo.Var(model.crops, domain=pyo.Binary)

    model.obj = pyo.Objective(
        expr=sum(values[i] * model.x[i] for i in model.crops),
        sense=pyo.maximize,
    )
    model.cap = pyo.Constraint(
        expr=sum(weights[i] * model.x[i] for i in model.crops) <= capacity
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}