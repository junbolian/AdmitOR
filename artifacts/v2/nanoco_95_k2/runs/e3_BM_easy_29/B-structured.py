# IR: {"sets":{"stations":"0..9","corridors":[[0,6],[0,8],[1,3],[1,6],[1,7],[1,9],[2,6],[2,8],[2,9],[3,7],[4,5],[4,7],[4,8],[4,9],[5,6],[5,9],[6,8]]},"params":{"edge_weights":"real score per corridor, in listed order","station_capacities":"capacity upper bound per station, in station order"},"variables":{"selected[i,j]":"binary for each listed corridor"},"constraints":["For each station s: sum(selected[i,j] for corridors incident to s) <= station_capacities[s]."],"objective":"Maximize sum(edge_weights[i,j] * selected[i,j] over listed corridors)."}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    corridors = (
        (0, 6),
        (0, 8),
        (1, 3),
        (1, 6),
        (1, 7),
        (1, 9),
        (2, 6),
        (2, 8),
        (2, 9),
        (3, 7),
        (4, 5),
        (4, 7),
        (4, 8),
        (4, 9),
        (5, 6),
        (5, 9),
        (6, 8),
    )
    stations = range(10)

    edge_weights = params["edge_weights"]
    station_capacities = params["station_capacities"]

    if len(edge_weights) != len(corridors):
        raise ValueError("edge_weights must contain exactly 17 entries.")
    if len(station_capacities) != len(stations):
        raise ValueError("station_capacities must contain exactly 10 entries.")

    model = pyo.ConcreteModel()

    model.stations = pyo.Set(initialize=stations, ordered=True)
    model.corridors = pyo.Set(
        initialize=corridors, dimen=2, ordered=True
    )

    model.edge_scores = pyo.Param(
        model.corridors,
        initialize={
            corridor: edge_weights[position]
            for position, corridor in enumerate(corridors)
        },
        within=pyo.Reals,
    )
    model.dispatch_limits = pyo.Param(
        model.stations,
        initialize={
            station: station_capacities[station]
            for station in stations
        },
        within=pyo.Reals,
    )

    model.selected = pyo.Var(model.corridors, domain=pyo.Binary)

    def capacity_rule(instance, station):
        return (
            sum(
                instance.selected[first, second]
                for first, second in corridors
                if station == first or station == second
            )
            <= instance.dispatch_limits[station]
        )

    model.station_capacity_constraints = pyo.Constraint(
        model.stations, rule=capacity_rule
    )

    model.total_efficiency = pyo.Objective(
        expr=sum(
            model.edge_scores[first, second]
            * model.selected[first, second]
            for first, second in corridors
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "infeasible_or_failed"}

    try:
        obj_val = float(pyo.value(model.total_efficiency))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}