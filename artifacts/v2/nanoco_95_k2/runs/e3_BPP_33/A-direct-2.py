import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    sizes = params["memory_sizes"]
    cap = params["block_capacity"]

    n = len(sizes)
    items = list(range(n))
    blocks = list(range(n))

    big_m = float(sum(sizes))

    model = pyo.ConcreteModel()

    model.I = pyo.Set(initialize=items)
    model.B = pyo.Set(initialize=blocks)

    model.x = pyo.Var(model.I, model.B, domain=pyo.Binary)
    model.y = pyo.Var(model.B, domain=pyo.Binary)

    model.obj = pyo.Objective(expr=sum(model.y[b] for b in model.B), sense=pyo.minimize)

    model.assign = pyo.Constraint(
        model.I, rule=lambda model, i: sum(model.x[i, b] for b in model.B) == 1
    )
    model.capacity = pyo.Constraint(
        model.B,
        rule=lambda model, b: sum(sizes[i] * model.x[i, b] for i in model.I)
        <= cap * model.y[b],
    )
    model.link = pyo.Constraint(
        model.I,
        model.B,
        rule=lambda model, i, b: model.x[i, b] <= model.y[b],
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}