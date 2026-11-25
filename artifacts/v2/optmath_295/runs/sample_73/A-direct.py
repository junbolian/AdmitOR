import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    capacity = params["capacity"]
    values = params["values"]
    weights = params["weights"]

    n = len(values)
    items = range(n)

    model = pyo.ConcreteModel()
    model.x = pyo.Var(items, domain=pyo.Binary)

    model.obj = pyo.Objective(
        expr=sum(values[i] * model.x[i] for i in items),
        sense=pyo.maximize,
    )

    model.weight_limit = pyo.Constraint(
        expr=sum(weights[i] * model.x[i] for i in items) <= capacity
    )

    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.obj))
    except Exception as exc:
        return {"objective": None, "status": "infeasible or solver failure: " + str(exc)}

    return {"objective": obj_val, "status": "optimal"}