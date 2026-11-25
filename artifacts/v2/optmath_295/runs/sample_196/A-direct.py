import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    capacity = params["truck_capacity"]
    weights = params["good_weights"]

    n_goods = len(weights)
    n_trucks = n_goods  # one truck per good is always feasible

    goods = range(n_goods)
    trucks = range(n_trucks)

    model = pyo.ConcreteModel()

    model.x = pyo.Var(goods, trucks, domain=pyo.Binary)
    model.y = pyo.Var(trucks, domain=pyo.Binary)

    model.assign = pyo.Constraint(
        goods, rule=lambda m, i: sum(m.x[i, j] for j in trucks) == 1
    )

    model.capacity_con = pyo.Constraint(
        trucks,
        rule=lambda m, j: sum(weights[i] * m.x[i, j] for i in goods)
        <= capacity * m.y[j],
    )

    model.link = pyo.Constraint(
        goods,
        trucks,
        rule=lambda m, i, j: m.x[i, j] <= m.y[j],
    )

    model.obj = pyo.Objective(expr=sum(model.y[j] for j in trucks), sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}