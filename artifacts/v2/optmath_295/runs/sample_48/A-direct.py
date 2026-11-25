import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    values = params["values"]
    weights = params["weights"]
    capacity = params["capacity"]

    items = list(range(len(values)))

    model = pyo.ConcreteModel()

    model.x = pyo.Var(items, domain=pyo.Binary)

    model.weight_constraint = pyo.Constraint(
        expr=sum(weights[i] * model.x[i] for i in items) <= capacity
    )

    model.obj = pyo.Objective(
        expr=sum(values[i] * model.x[i] for i in items),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.obj))
    except Exception:
        return {"objective": None, "status": "infeasible or unsolvable"}

    return {"objective": obj_val, "status": "optimal"}