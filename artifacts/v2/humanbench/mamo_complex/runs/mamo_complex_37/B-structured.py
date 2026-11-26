# IR: {"sets":{"V":"0..7","A":"[(i,j) for i in V for j in V if i!=j] in lexicographic order","T":"1..6"},"params":{"capacities":"nonnegative vector from params['capacities'], indexed in A order"},"variables":{"flow[i,j]":"nonnegative continuous for (i,j) in A"},"constraints":["flow[i,j] <= capacities[i,j] for (i,j) in A","sum(flow[k,j] for j!=k) == sum(flow[i,k] for i!=k) for k in T"],"objective":"maximize sum(flow[0,j] for j!=0) - sum(flow[i,0] for i!=0)"}

import pyomo.environ as pyo
from pyomo.common.errors import ApplicationError
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    vertices = list(range(8))
    arcs = [
        (origin, destination)
        for origin in vertices
        for destination in vertices
        if origin != destination
    ]
    capacities = list(params["capacities"])

    if len(capacities) != len(arcs):
        return {"objective": None, "status": "invalid_capacities_length"}

    model = pyo.ConcreteModel()

    model.vertices = pyo.Set(initialize=vertices, ordered=True)
    model.arcs = pyo.Set(initialize=arcs, dimen=2, ordered=True)
    model.transit_vertices = pyo.Set(initialize=range(1, 7), ordered=True)

    model.capacity = pyo.Param(
        model.arcs,
        initialize=dict(zip(arcs, capacities)),
        within=pyo.NonNegativeReals,
    )
    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    def capacity_rule(network, origin, destination):
        return (
            network.flow[origin, destination]
            <= network.capacity[origin, destination]
        )

    model.capacity_limits = pyo.Constraint(
        model.arcs, rule=capacity_rule
    )

    def conservation_rule(network, station):
        return sum(
            network.flow[station, destination]
            for destination in network.vertices
            if destination != station
        ) == sum(
            network.flow[origin, station]
            for origin in network.vertices
            if origin != station
        )

    model.flow_conservation = pyo.Constraint(
        model.transit_vertices, rule=conservation_rule
    )

    model.total_flow = pyo.Objective(
        expr=sum(
            model.flow[0, destination]
            for destination in model.vertices
            if destination != 0
        )
        - sum(
            model.flow[origin, 0]
            for origin in model.vertices
            if origin != 0
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except (ApplicationError, RuntimeError):
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_flow))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}