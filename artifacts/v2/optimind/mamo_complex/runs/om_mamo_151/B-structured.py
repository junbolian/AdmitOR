# IR: {"sets":{"V":"{0,...,8}","I":"{1,...,7}","A":"{(i,j) in V x V: i != j} minus {(2,1),(3,2),(7,3)}"},"params":{"capacity[i,j]":"params[f'capacity_{i}_{j}'] for every (i,j) in A"},"variables":{"flow[i,j]":"continuous, nonnegative, for (i,j) in A"},"constraints":["flow[i,j] <= capacity[i,j] for every (i,j) in A","sum(flow[i,j] for outgoing arcs) = sum(flow[j,i] for incoming arcs) for every i in I"],"objective":"maximize sum(flow[0,j] for outgoing source arcs) - sum(flow[i,0] for incoming source arcs)"}

import pyomo.environ as pyo
from pyomo.common.errors import ApplicationError
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    vertices = tuple(range(9))
    missing_arcs = {(2, 1), (3, 2), (7, 3)}
    arcs = tuple(
        (origin, destination)
        for origin in vertices
        for destination in vertices
        if origin != destination
        and (origin, destination) not in missing_arcs
    )

    outgoing = {
        vertex: tuple(
            destination
            for origin, destination in arcs
            if origin == vertex
        )
        for vertex in vertices
    }
    incoming = {
        vertex: tuple(
            origin
            for origin, destination in arcs
            if destination == vertex
        )
        for vertex in vertices
    }

    model = pyo.ConcreteModel()
    model.reservoirs = pyo.Set(initialize=vertices, ordered=True)
    model.intermediate_reservoirs = pyo.Set(
        initialize=range(1, 8), ordered=True
    )
    model.transfer_arcs = pyo.Set(
        dimen=2, initialize=arcs, ordered=True
    )

    model.transfer_capacity = pyo.Param(
        model.transfer_arcs,
        initialize={
            (origin, destination): params[
                f"capacity_{origin}_{destination}"
            ]
            for origin, destination in arcs
        },
        within=pyo.Reals,
    )

    model.flow = pyo.Var(
        model.transfer_arcs,
        domain=pyo.NonNegativeReals,
    )

    def capacity_rule(mdl, origin, destination):
        return (
            mdl.flow[origin, destination]
            <= mdl.transfer_capacity[origin, destination]
        )

    model.capacity_limits = pyo.Constraint(
        model.transfer_arcs,
        rule=capacity_rule,
    )

    def conservation_rule(mdl, vertex):
        return (
            pyo.quicksum(
                mdl.flow[vertex, destination]
                for destination in outgoing[vertex]
            )
            == pyo.quicksum(
                mdl.flow[origin, vertex]
                for origin in incoming[vertex]
            )
        )

    model.flow_conservation = pyo.Constraint(
        model.intermediate_reservoirs,
        rule=conservation_rule,
    )

    model.total_transfer = pyo.Objective(
        expr=(
            pyo.quicksum(
                model.flow[0, destination]
                for destination in outgoing[0]
            )
            - pyo.quicksum(
                model.flow[origin, 0]
                for origin in incoming[0]
            )
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except (RuntimeError, ApplicationError):
        return {"objective": None, "status": "infeasible_or_failed"}

    try:
        obj_val = float(pyo.value(model.total_transfer))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}