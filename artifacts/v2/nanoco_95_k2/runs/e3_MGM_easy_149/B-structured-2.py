# IR: {"sets":{"V":[0,1,2,3,4,5,6,7],"E":[[0,1],[0,4],[0,5],[1,2],[1,3],[1,4],[1,5],[1,6],[1,7],[2,5],[3,4],[3,7],[4,6],[4,7],[5,6],[5,7],[6,7]]},"params":{},"variables":{"x[i,j]":{"domain":"Binary","indices":"(i,j) in E"}},"constraints":["For each v in V: sum(x[i,j] for (i,j) in E if i == v or j == v) <= 1"],"objective":{"sense":"maximize","expression":"sum(x[i,j] for (i,j) in E)"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve the maximum-cardinality matching problem; no parameters are required."""
    vertices = range(8)
    edges = [
        (0, 1), (0, 4), (0, 5),
        (1, 2), (1, 3), (1, 4), (1, 5), (1, 6), (1, 7),
        (2, 5),
        (3, 4), (3, 7),
        (4, 6), (4, 7),
        (5, 6), (5, 7),
        (6, 7),
    ]

    model = pyo.ConcreteModel()
    model.vertices = pyo.Set(initialize=vertices, ordered=True)
    model.edges = pyo.Set(dimen=2, initialize=edges, ordered=True)
    model.x = pyo.Var(model.edges, domain=pyo.Binary)

    def exclusive_assignment_rule(instance, vertex):
        return sum(
            instance.x[source, target]
            for source, target in instance.edges
            if source == vertex or target == vertex
        ) <= 1

    model.exclusive_assignment = pyo.Constraint(
        model.vertices, rule=exclusive_assignment_rule
    )
    model.total_matches = pyo.Objective(
        expr=sum(model.x[source, target] for source, target in model.edges),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_matches))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}