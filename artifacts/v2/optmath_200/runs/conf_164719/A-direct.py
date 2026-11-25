import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    capacity = params["capacity"]
    values = params["values"]
    weights = params["weights"]

    n = len(values)
    items = list(range(n))

    model = pyo.ConcreteModel()

    model.x = pyo.Var(items, domain=pyo.Binary)

    model.value_expr = pyo.Objective(
        expr=sum(values[i] * model.x[i] for i in items),
        sense=pyo.maximize,
    )

    model.weight_constraint = pyo.Constraint(
        expr=sum(weights[i] * model.x[i] for i in items) <= capacity
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.value_expr))
    return {"objective": obj_val, "status": "optimal"}