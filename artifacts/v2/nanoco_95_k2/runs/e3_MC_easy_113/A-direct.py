import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    arc_capacities = params["arc_capacities"]
    arc_unit_costs = params["arc_unit_costs"]
    num_nodes = params["num_nodes"]
    source = params["source"]
    sink = params["sink"]

    # Arc list (topology is structural, as in the problem statement)
    arcs = [
        (0, 1), (0, 2), (0, 3), (0, 7),
        (1, 2), (1, 5),
        (2, 3), (2, 5), (2, 6),
        (3, 4), (3, 5),
        (4, 5), (4, 6), (4, 7),
        (5, 6), (5, 7),
        (6, 7),
    ]

    model = pyo.ConcreteModel()

    model.nodes = pyo.RangeSet(0, num_nodes - 1)
    model.arcs = pyo.Set(initialize=arcs, dimen=2)

    # y[i] = 1 if node i is in the protected zone T (sink side), 0 if in S
    model.y = pyo.Var(model.nodes, domain=pyo.Binary)

    model.cap = pyo.Constraint(
        model.nodes,
        rule=lambda m, i: m.y[i] == 0 if i == source else (m.y[i] == 1 if i == sink else pyo.Constraint.Skip)
    )

    # x[a] = 1 if arc crosses from S to T
    model.x = pyo.Var(model.arcs, domain=pyo.Binary)

    def cross_rule(m, i, j):
        return m.x[i, j] >= m.y[j] - m.y[i]

    model.cross = pyo.Constraint(model.arcs, rule=cross_rule)

    def obj_rule(m):
        return sum(arc_capacities[k] * m.x[i, j] for k, (i, j) in enumerate(arcs))

    model.min_cut = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.min_cut))
    return {"objective": obj_val, "status": "optimal"}