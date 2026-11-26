# IR: {"sets":{"H":"{0,...,7}","T":"{1,...,6}","A":"{(i,j): i in {0,...,6}, j in H, i != j, (i,j) not in {(3,7),(4,3)}}"},"params":{"capacity[i,j]":"params[f'capacity_{i}_{j}'] for (i,j) in A"},"variables":{"flow[i,j]":"continuous, nonnegative, for (i,j) in A"},"constraints":["flow[i,j] <= capacity[i,j] for (i,j) in A","sum(flow[i,k] for (i,k) in A) = sum(flow[k,j] for (k,j) in A) for k in T"],"objective":"maximize sum(flow[0,j] for (0,j) in A) - sum(flow[i,0] for (i,0) in A)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    hubs = tuple(range(8))
    intermediate_hubs = tuple(range(1, 7))
    arcs = tuple(
        (origin, destination)
        for origin in range(7)
        for destination in hubs
        if origin != destination
        and (origin, destination) not in {(3, 7), (4, 3)}
    )

    incoming = {
        hub: tuple(arc for arc in arcs if arc[1] == hub)
        for hub in hubs
    }
    outgoing = {
        hub: tuple(arc for arc in arcs if arc[0] == hub)
        for hub in hubs
    }

    model = pyo.ConcreteModel()
    model.hubs = pyo.Set(initialize=hubs)
    model.intermediate_hubs = pyo.Set(initialize=intermediate_hubs)
    model.arcs = pyo.Set(dimen=2, initialize=arcs)

    model.capacity = pyo.Param(
        model.arcs,
        initialize={
            (origin, destination): params[f"capacity_{origin}_{destination}"]
            for origin, destination in arcs
        },
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

    def conservation_rule(network, hub):
        return (
            sum(network.flow[arc] for arc in incoming[hub])
            == sum(network.flow[arc] for arc in outgoing[hub])
        )

    model.flow_conservation = pyo.Constraint(
        model.intermediate_hubs, rule=conservation_rule
    )

    model.total_flow = pyo.Objective(
        expr=(
            sum(model.flow[arc] for arc in outgoing[0])
            - sum(model.flow[arc] for arc in incoming[0])
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as error:
        # Appsi raises this when it cannot load a feasible solution.
        # Preserve unexpected solver exceptions.
        if "A feasible solution was not found" not in str(error):
            raise

    try:
        obj_val = float(pyo.value(model.total_flow))
    except (ValueError, TypeError):
        return {"objective": None, "status": "no_solution"}

    return {"objective": obj_val, "status": "optimal"}