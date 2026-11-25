# IR: {"sets":{"V":[0,1,2,3,4,5,6,7],"E":[[0,1],[0,3],[0,5],[0,6],[0,7],[1,2],[1,4],[1,5],[1,6],[2,4],[2,7],[3,4],[4,5],[4,6],[4,7],[5,7],[6,7]]},"params":{},"variables":{"x[u,v]":{"index":"(u,v) in E","type":"binary"}},"constraints":["For each station s in V: sum(x[u,v] for (u,v) in E if u == s or v == s) <= 1"],"objective":{"sense":"maximize","expression":"sum(x[u,v] for (u,v) in E)"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Return the maximum matching cardinality for the specified fixed graph."""
    model = pyo.ConcreteModel()

    model.stations = pyo.Set(initialize=range(8), ordered=True)
    model.corridors = pyo.Set(
        dimen=2,
        ordered=True,
        initialize=[
            (0, 1),
            (0, 3),
            (0, 5),
            (0, 6),
            (0, 7),
            (1, 2),
            (1, 4),
            (1, 5),
            (1, 6),
            (2, 4),
            (2, 7),
            (3, 4),
            (4, 5),
            (4, 6),
            (4, 7),
            (5, 7),
            (6, 7),
        ],
    )

    model.selected = pyo.Var(model.corridors, domain=pyo.Binary)

    def station_capacity_rule(instance, station):
        return sum(
            instance.selected[source, target]
            for source, target in instance.corridors
            if source == station or target == station
        ) <= 1

    model.station_capacity = pyo.Constraint(
        model.stations, rule=station_capacity_rule
    )

    model.matching_cardinality = pyo.Objective(
        expr=sum(
            model.selected[source, target]
            for source, target in model.corridors
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "a feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.matching_cardinality))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}