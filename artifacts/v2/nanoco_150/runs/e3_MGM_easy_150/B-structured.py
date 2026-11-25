# IR: {"sets":{"V":"{0,...,10}","E":[[0,1],[0,4],[0,5],[0,7],[1,6],[1,10],[2,4],[2,7],[2,10],[3,6],[4,5],[4,6],[4,8],[5,7],[6,9],[7,8]]},"params":{},"variables":{"x[e]":"binary for e in E"},"constraints":["For each v in V: sum(x[e] for e in E incident to v) <= 1"],"objective":"maximize sum(x[e] for e in E)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.teams = pyo.RangeSet(0, 10)
    model.edges = pyo.Set(
        dimen=2,
        initialize=[
            (0, 1),
            (0, 4),
            (0, 5),
            (0, 7),
            (1, 6),
            (1, 10),
            (2, 4),
            (2, 7),
            (2, 10),
            (3, 6),
            (4, 5),
            (4, 6),
            (4, 8),
            (5, 7),
            (6, 9),
            (7, 8),
        ],
    )

    model.x = pyo.Var(model.edges, domain=pyo.Binary)

    def team_capacity_rule(block, team):
        return sum(
            block.x[left, right]
            for left, right in block.edges
            if left == team or right == team
        ) <= 1

    model.team_capacity = pyo.Constraint(
        model.teams,
        rule=team_capacity_rule,
    )

    model.total_assignments = pyo.Objective(
        expr=sum(model.x[left, right] for left, right in model.edges),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_assignments))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}