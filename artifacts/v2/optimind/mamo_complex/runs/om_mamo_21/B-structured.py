# IR: {"sets":{"V":[0,1,2,3,4,5],"A":"{(i,j) in V x V: i != j}","T":[1,2,3,4]},"params":{"capacity_matrix":"nonnegative directed capacities from params['capacity_matrix']"},"variables":{"flow[i,j]":"continuous nonnegative, (i,j) in A"},"constraints":["flow[i,j] <= capacity_matrix[i][j] for (i,j) in A","sum(flow[v,j] for j != v) = sum(flow[i,v] for i != v) for v in T"],"objective":"maximize sum(flow[0,j] for j != 0) - sum(flow[i,0] for i != 0)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    capacity_matrix = params["capacity_matrix"]

    model = pyo.ConcreteModel()
    model.stations = pyo.RangeSet(0, 5)
    model.transit_stations = pyo.RangeSet(1, 4)
    model.arcs = pyo.Set(
        dimen=2,
        initialize=[
            (origin, destination)
            for origin in range(6)
            for destination in range(6)
            if origin != destination
        ],
    )

    model.capacity = pyo.Param(
        model.stations,
        model.stations,
        initialize=lambda mdl, origin, destination: capacity_matrix[origin][destination],
        within=pyo.NonNegativeReals,
    )

    def flow_bounds(mdl, origin, destination):
        return (0, mdl.capacity[origin, destination])

    model.flow = pyo.Var(
        model.arcs,
        domain=pyo.NonNegativeReals,
        bounds=flow_bounds,
    )

    def conservation_rule(mdl, station):
        outgoing = sum(
            mdl.flow[station, destination]
            for destination in mdl.stations
            if destination != station
        )
        incoming = sum(
            mdl.flow[origin, station]
            for origin in mdl.stations
            if origin != station
        )
        return outgoing == incoming

    model.flow_conservation = pyo.Constraint(
        model.transit_stations,
        rule=conservation_rule,
    )

    model.total_flow = pyo.Objective(
        expr=(
            sum(
                model.flow[0, destination]
                for destination in model.stations
                if destination != 0
            )
            - sum(
                model.flow[origin, 0]
                for origin in model.stations
                if origin != 0
            )
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_flow))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}