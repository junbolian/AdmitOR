import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost = params["assignment_cost"]

    n_dev = len(cost)
    n_bug = len(cost[0])

    model = pyo.ConcreteModel()

    model.dev = pyo.RangeSet(0, n_dev - 1)
    model.bug = pyo.RangeSet(0, n_bug - 1)

    model.x = pyo.Var(model.dev, model.bug, domain=pyo.Binary)

    model.obj = pyo.Objective(
        expr=sum(cost[i][j] * model.x[i, j] for i in model.dev for j in model.bug),
        sense=pyo.minimize,
    )

    model.dev_once = pyo.Constraint(
        model.dev,
        rule=lambda m, i: sum(m.x[i, j] for j in m.bug) == 1,
    )
    model.bug_once = pyo.Constraint(
        model.bug,
        rule=lambda m, j: sum(m.x[i, j] for i in m.dev) == 1,
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}