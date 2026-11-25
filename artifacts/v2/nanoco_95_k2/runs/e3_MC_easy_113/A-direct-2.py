import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    arc_capacities = params["arc_capacities"]
    num_nodes = params["num_nodes"]
    source = params["source"]
    sink = params["sink"]

    arcs = [
        (0, 1), (0, 2), (0, 3), (0, 7),
        (1, 2), (1, 5), (2, 3), (2, 5),
        (2, 6), (3, 4), (3, 5), (4, 5),
        (4, 6), (4, 7), (5, 6), (5, 7),
        (6, 7),
    ]
    cap = {arcs[k]: arc_capacities[k] for k in range(len(arcs))}

    nodes = list(range(num_nodes))
    model = pyo.ConcreteModel()
    model.N = pyo.Set(initialize=nodes)
    model.A = pyo.Set(initialize=arcs, dimen=2)

    model.y = pyo.Var(model.N, domain=pyo.Binary)

    def cut_rule(mdl, i, j):
        return mdl.y[i] - mdl.y[j] <= 0
    model.cut_con = pyo.Constraint(model.A, rule=cut_rule)

    model.source_fix = pyo.Constraint(expr=model.y[source] == 1)
    model.sink_fix = pyo.Constraint(expr=model.y[sink] == 0)

    def obj_rule(mdl):
        return sum(cap[(i, j)] * (mdl.y[i] - mdl.y[j]) for (i, j) in arcs)
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))

    return {"objective": obj_val, "status": "optimal"}