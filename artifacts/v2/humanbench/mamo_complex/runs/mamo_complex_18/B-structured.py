# IR: {"sets":{"V":"range(num_stations)","A":"[(i,j) for i in V for j in V if i!=j], row-major","T":"V excluding 0 and num_stations-1"},"params":{"num_stations":"params['num_stations']","capacities":"params['capacities'], one nonnegative capacity per arc in A"},"variables":{"flow[i,j]":"continuous nonnegative for (i,j) in A"},"constraints":["flow[i,j] <= capacities[position(i,j)] for each (i,j) in A","sum(flow[i,v] for i!=v) = sum(flow[v,j] for j!=v) for each v in T"],"objective":"maximize sum(flow[0,j] for j!=0) - sum(flow[i,0] for i!=0), in thousands of gallons/hour"}

import operator

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_stations = operator.index(params["num_stations"])
    capacities = list(params["capacities"])

    if num_stations < 2:
        return {"objective": None, "status": "invalid_station_count"}

    stations = list(range(num_stations))
    arcs = [
        (origin, destination)
        for origin in stations
        for destination in stations
        if origin != destination
    ]

    if len(capacities) != len(arcs):
        return {"objective": None, "status": "invalid_capacity_count"}

    capacity_by_arc = dict(zip(arcs, capacities))

    model = pyo.ConcreteModel()
    model.stations = pyo.Set(initialize=stations, ordered=True)
    model.arcs = pyo.Set(initialize=arcs, dimen=2, ordered=True)
    model.transit_stations = pyo.Set(
        initialize=stations[1:-1], ordered=True
    )

    model.pipeline_capacity = pyo.Param(
        model.arcs,
        initialize=capacity_by_arc,
        within=pyo.NonNegativeReals,
    )
    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    def capacity_rule(network, origin, destination):
        return (
            network.flow[origin, destination]
            <= network.pipeline_capacity[origin, destination]
        )

    model.capacity_limits = pyo.Constraint(
        model.arcs, rule=capacity_rule
    )

    def conservation_rule(network, station):
        incoming = sum(
            network.flow[origin, station]
            for origin in stations
            if origin != station
        )
        outgoing = sum(
            network.flow[station, destination]
            for destination in stations
            if destination != station
        )
        return incoming == outgoing

    model.flow_conservation = pyo.Constraint(
        model.transit_stations, rule=conservation_rule
    )

    model.maximum_flow = pyo.Objective(
        expr=(
            sum(
                model.flow[0, destination]
                for destination in stations
                if destination != 0
            )
            - sum(
                model.flow[origin, 0]
                for origin in stations
                if origin != 0
            )
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.maximum_flow))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}