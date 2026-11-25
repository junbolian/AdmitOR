import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    nodes = [0, 1, 2, 3, 4]
    pairs = [(i, j) for i in nodes for j in nodes if i != j]

    model = pyo.ConcreteModel()

    model.x = pyo.Var(nodes, domain=pyo.Binary)
    model.y = pyo.Var(pairs, domain=pyo.Binary)

    benefit = {}
    for i in nodes:
        for j in nodes:
            if i != j:
                benefit[(i, j)] = params["coverage_benefit_%d%d" % (i, j)]

    model.pair_link = pyo.ConstraintList()
    for (i, j) in pairs:
        model.pair_link.add(model.y[(i, j)] <= model.x[i])
        model.pair_link.add(model.y[(i, j)] <= model.x[j])
        model.pair_link.add(model.y[(i, j)] >= model.x[i] + model.x[j] - 1)

    model.selection = pyo.Constraint(
        expr=sum(model.x[i] for i in nodes) == params["num_centers_to_select"]
    )

    model.obj = pyo.Objective(
        expr=sum(benefit[(i, j)] * model.y[(i, j)] for (i, j) in pairs),
        sense=pyo.maximize,
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}