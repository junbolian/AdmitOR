import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    nodes = [0, 1, 2, 3]
    dispersions = {
        (0, 1): params["d01"],
        (0, 2): params["d02"],
        (0, 3): params["d03"],
        (1, 0): params["d10"],
        (1, 2): params["d12"],
        (1, 3): params["d13"],
        (2, 0): params["d20"],
        (2, 1): params["d21"],
        (2, 3): params["d23"],
        (3, 0): params["d30"],
        (3, 1): params["d31"],
        (3, 2): params["d32"],
    }
    arcs = list(dispersions.keys())

    model = pyo.ConcreteModel()
    model.nodes = pyo.Set(initialize=nodes)
    model.arcs = pyo.Set(initialize=arcs, dimen=2)

    model.x = pyo.Var(model.nodes, domain=pyo.Binary)
    model.y = pyo.Var(model.arcs, domain=pyo.Binary)

    model.total_dispersion = pyo.Objective(
        expr=sum(dispersions[i, j] * model.y[i, j] for (i, j) in arcs),
        sense=pyo.maximize,
    )

    model.select_exactly_three = pyo.Constraint(
        expr=sum(model.x[i] for i in nodes) == 3
    )

    def pairwise_rule(model, i, j):
        return model.y[i, j] <= model.x[i]

    model.pairwise_first = pyo.Constraint(model.arcs, rule=pairwise_rule)

    def pairwise_rule2(model, i, j):
        return model.y[i, j] <= model.x[j]

    model.pairwise_second = pyo.Constraint(model.arcs, rule=pairwise_rule2)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_dispersion))
    return {"objective": obj_val, "status": "optimal"}