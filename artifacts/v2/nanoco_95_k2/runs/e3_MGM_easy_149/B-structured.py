# IR: {"sets":{"V":[0,1,2,3,4,5,6,7],"E":[[0,1],[0,4],[0,5],[1,2],[1,3],[1,4],[1,5],[1,6],[1,7],[2,5],[3,4],[3,7],[4,6],[4,7],[5,6],[5,7],[6,7]]},"params":{},"variables":{"x[e]":{"index":"e in E","type":"binary"}},"constraints":["For each v in V: sum(x[i,j] for (i,j) in E if v in (i,j)) <= 1"],"objective":{"sense":"maximize","expression":"sum(x[e] for e in E)"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.vertices = pyo.Set(initialize=range(8), ordered=True)
    model.edges = pyo.Set(
        dimen=2,
        initialize=[
            (0, 1),
            (0, 4),
            (0, 5),
            (1, 2),
            (1, 3),
            (1, 4),
            (1, 5),
            (1, 6),
            (1, 7),
            (2, 5),
            (3, 4),
            (3, 7),
            (4, 6),
            (4, 7),
            (5, 6),
            (5, 7),
            (6, 7),
        ],
        ordered=True,
    )

    model.x = pyo.Var(model.edges, domain=pyo.Binary)

    def hub_capacity_rule(instance, vertex):
        return sum(
            instance.x[first, second]
            for first, second in instance.edges
            if vertex == first or vertex == second
        ) <= 1

    model.hub_capacity = pyo.Constraint(
        model.vertices, rule=hub_capacity_rule
    )
    model.matching_size = pyo.Objective(
        expr=sum(model.x[first, second] for first, second in model.edges),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.matching_size))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}