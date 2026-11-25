import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()
    n = 9
    model.Items = pyo.RangeSet(0, n - 1)

    values = [params[f"value_{idx}"] for idx in range(n)]
    weights = [params[f"weight_{idx}"] for idx in range(n)]
    capacity = params["capacity"]

    model.x = pyo.Var(model.Items, domain=pyo.Binary)

    model.value = pyo.Objective(
        expr=sum(values[idx] * model.x[idx] for idx in model.Items),
        sense=pyo.maximize,
    )

    model.capacity_rule = pyo.Constraint(
        expr=sum(weights[idx] * model.x[idx] for idx in model.Items) <= capacity
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.value))
    return {"objective": obj_val, "status": "optimal"}