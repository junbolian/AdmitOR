import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    arc_capacities = params["arc_capacities"]

    arcs = [
        (0, 1), (0, 6), (0, 8),
        (1, 2),
        (2, 3), (2, 7),
        (3, 4),
        (4, 5), (4, 7), (4, 8),
        (5, 6),
        (6, 7), (6, 8),
        (7, 8),
        (8, 9),
    ]
    nodes = list(range(10))
    source = 0
    sink = 9

    cap = {(i, j): arc_capacities[k] for k, (i, j) in enumerate(arcs)}

    model = pyo.ConcreteModel()
    model.nodes = pyo.Set(initialize=nodes)
    model.arcs = pyo.Set(initialize=arcs, dimen=2)

    # x[i] = 1 if node i is on the source side
    model.x = pyo.Var(model.nodes, domain=pyo.Binary)

    model.source_side = pyo.Constraint(expr=model.x[source] == 1)
    model.sink_side = pyo.Constraint(expr=model.x[sink] == 0)

    def cut_expr(m):
        return sum(
            cap[(i, j)] * (m.x[i] - m.x[j])
            for (i, j) in arcs
        )

    model.obj = pyo.Objective(rule=cut_expr, sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}