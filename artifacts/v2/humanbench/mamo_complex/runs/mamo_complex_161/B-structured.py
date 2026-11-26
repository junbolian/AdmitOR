# IR: {"sets":{"N":"{0,...,8}","A":"[(i,j) in N x N, lexicographic order, i != j and (i,j) != (1,5)]","R":"N \\ {0,8}"},"params":{"capacity":"params['capacity'][k] is the nonnegative capacity of A[k]"},"variables":{"flow[i,j]":"continuous nonnegative for (i,j) in A"},"constraints":["flow[i,j] <= capacity[i,j] for (i,j) in A","sum(flow[i,j] for outgoing arcs) = sum(flow[j,i] for incoming arcs) for i in R"],"objective":"maximize sum(flow[0,j]) - sum(flow[j,0])"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    nodes = range(9)
    arcs = [
        (origin, destination)
        for origin in nodes
        for destination in nodes
        if origin != destination and (origin, destination) != (1, 5)
    ]

    capacities = list(params["capacity"])
    if len(capacities) != len(arcs):
        raise ValueError(
            f"capacity must contain exactly {len(arcs)} entries in the specified order."
        )

    incoming = {
        station: [
            (origin, destination)
            for origin, destination in arcs
            if destination == station
        ]
        for station in nodes
    }
    outgoing = {
        station: [
            (origin, destination)
            for origin, destination in arcs
            if origin == station
        ]
        for station in nodes
    }

    model = pyo.ConcreteModel()
    model.stations = pyo.Set(initialize=nodes, ordered=True)
    model.arcs = pyo.Set(initialize=arcs, dimen=2, ordered=True)
    model.relay_stations = pyo.Set(initialize=range(1, 8), ordered=True)

    model.arc_capacity = pyo.Param(
        model.arcs,
        initialize=dict(zip(arcs, capacities)),
        within=pyo.NonNegativeReals,
    )
    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    def capacity_rule(network, origin, destination):
        return (
            network.flow[origin, destination]
            <= network.arc_capacity[origin, destination]
        )

    model.capacity_limits = pyo.Constraint(model.arcs, rule=capacity_rule)

    def conservation_rule(network, station):
        return sum(
            network.flow[arc] for arc in outgoing[station]
        ) == sum(
            network.flow[arc] for arc in incoming[station]
        )

    model.flow_conservation = pyo.Constraint(
        model.relay_stations, rule=conservation_rule
    )

    model.throughput = pyo.Objective(
        expr=(
            sum(model.flow[arc] for arc in outgoing[0])
            - sum(model.flow[arc] for arc in incoming[0])
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.throughput))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}