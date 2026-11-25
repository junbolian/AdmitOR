import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    edge_weights = params["edge_weights"]

    edges = [
        (0, 1), (0, 2), (1, 3), (1, 4), (1, 5),
        (2, 7), (3, 4), (3, 5), (4, 5), (4, 6),
        (4, 7), (5, 6),
    ]

    num_nets = 8
    nets = list(range(num_nets))

    edge_index = pyo.Set(initialize=list(range(len(edges))), ordered=True)

    # Large constant for big-M formulation
    big_M = sum(edge_weights) + 1
    max_possible = sum(edge_weights)

    model = pyo.ConcreteModel()

    model.nets = pyo.Set(initialize=nets, ordered=True)

    # Non-negative integer track assignments
    model.track = pyo.Var(
        model.nets, domain=pyo.NonNegativeIntegers, bounds=(0, max_possible)
    )

    # Maximum track used
    model.max_track = pyo.Var(
        domain=pyo.NonNegativeIntegers, bounds=(0, max_possible)
    )

    # Binary orientation per edge
    model.y = pyo.Var(edge_index, domain=pyo.Binary)

    # Objective
    model.obj = pyo.Objective(expr=model.max_track, sense=pyo.minimize)

    # Each track <= max_track
    def max_track_rule(m, i):
        return m.track[i] <= m.max_track

    model.max_track_con = pyo.Constraint(model.nets, rule=max_track_rule)

    # Disjunctive separation: |track[u] - track[v]| >= d
    # y[e] = 1  =>  track[u] - track[v] >= d
    # y[e] = 0  =>  track[v] - track[u] >= d
    def sep_rule(m, e):
        i, j = edges[e]
        d = edge_weights[e]
        return m.track[i] - m.track[j] >= d - big_M * (1 - m.y[e])

    def sep_rev_rule(m, e):
        i, j = edges[e]
        d = edge_weights[e]
        return m.track[j] - m.track[i] >= d - big_M * m.y[e]

    model.sep = pyo.Constraint(edge_index, rule=sep_rule)
    model.sep_rev = pyo.Constraint(edge_index, rule=sep_rev_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))

    return {"objective": obj_val, "status": "optimal"}