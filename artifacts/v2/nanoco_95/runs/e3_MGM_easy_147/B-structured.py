# IR: {"sets":{"V":[0,1,2,3,4,5,6,7],"E":[[0,1],[0,2],[0,3],[0,4],[0,6],[0,7],[1,2],[1,3],[1,4],[1,5],[2,3],[3,5],[3,6],[3,7],[4,5],[5,6],[6,7]]},"params":{},"variables":{"x[i,j]":{"index":"(i,j) in E","type":"binary"}},"constraints":["For each v in V: sum(x[i,j] for (i,j) in E if v in (i,j)) <= 1."],"objective":{"sense":"maximize","expression":"sum(x[i,j] for (i,j) in E)"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve the maximum-cardinality matching problem; no parameters are required."""
    model = pyo.ConcreteModel()

    model.vertices = pyo.Set(initialize=range(8), ordered=True)
    model.edges = pyo.Set(
        dimen=2,
        ordered=True,
        initialize=[
            (0, 1), (0, 2), (0, 3), (0, 4), (0, 6), (0, 7),
            (1, 2), (1, 3), (1, 4), (1, 5),
            (2, 3),
            (3, 5), (3, 6), (3, 7),
            (4, 5),
            (5, 6),
            (6, 7),
        ],
    )

    model.selected = pyo.Var(model.edges, domain=pyo.Binary)

    def incidence_rule(instance, vertex):
        return sum(
            instance.selected[left, right]
            for left, right in instance.edges
            if vertex in (left, right)
        ) <= 1

    model.incidence_limit = pyo.Constraint(
        model.vertices, rule=incidence_rule
    )

    model.matching_cardinality = pyo.Objective(
        expr=sum(
            model.selected[left, right]
            for left, right in model.edges
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as error:
        if "a feasible solution was not found" in str(error).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.matching_cardinality))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}