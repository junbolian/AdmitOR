# IR: {"sets":{"stations":[0,1,2,3,4,5,6,7,8,9],"edges":[[0,6],[0,8],[1,3],[1,6],[1,7],[1,9],[2,6],[2,8],[2,9],[3,7],[4,5],[4,7],[4,8],[4,9],[5,6],[5,9],[6,8]]},"params":{"edge_weights":"real vector indexed by listed edge order","station_capacities":"real vector indexed by station"},"variables":{"selected[e]":"binary for each edge e"},"constraints":["For each station s: sum(selected[e] for edges incident to s) <= station_capacities[s]"],"objective":"maximize sum(edge_weights[e] * selected[e] for each edge e)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    edges = (
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

    edge_weights = params["edge_weights"]
    station_capacities = params["station_capacities"]

    model = pyo.ConcreteModel()
    model.stations = pyo.RangeSet(0, 9)
    model.edge_ids = pyo.RangeSet(0, len(edges) - 1)

    model.corridor_weights = pyo.Param(
        model.edge_ids,
        initialize={
            edge_id: edge_weights[edge_id]
            for edge_id in range(len(edges))
        },
        within=pyo.Reals,
    )
    model.dispatch_capacities = pyo.Param(
        model.stations,
        initialize={
            station: station_capacities[station]
            for station in range(10)
        },
        within=pyo.Reals,
    )

    model.selected = pyo.Var(model.edge_ids, domain=pyo.Binary)

    incident_edges = {
        station: tuple(
            edge_id
            for edge_id, endpoints in enumerate(edges)
            if station in endpoints
        )
        for station in range(10)
    }

    def capacity_rule(instance, station):
        return (
            sum(
                instance.selected[edge_id]
                for edge_id in incident_edges[station]
            )
            <= instance.dispatch_capacities[station]
        )

    model.station_capacity_limits = pyo.Constraint(
        model.stations,
        rule=capacity_rule,
    )

    model.total_efficiency = pyo.Objective(
        expr=sum(
            model.corridor_weights[edge_id] * model.selected[edge_id]
            for edge_id in model.edge_ids
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
        obj_val = float(pyo.value(model.total_efficiency))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}