# IR: {"sets":{"N":[0,1,2,3,4,5,6,7,8],"I":[1,2,3,4,5,6,7],"A":{"0":[1,2,3,4,5,6,7,8],"1":[0,3,4,5,6,7,8],"2":[0,1,3,4,5,6,7,8],"3":[0,2,4,5,6,7,8],"4":[0,1,2,3,5,6,7,8],"5":[2,3,4,6,7,8],"6":[0,1,2,3,7,8],"7":[0,1,2,3,4,5,6,8],"8":[0,1,3,4,5,6,7]}},"params":{"capacity[i,j]":"params['capacity_'+str(i)+'_'+str(j)] for (i,j) in A"},"variables":{"flow[i,j]":"continuous nonnegative for (i,j) in A"},"constraints":["flow[i,j] <= capacity[i,j] for (i,j) in A","sum(flow[i,v] for (i,v) in A) = sum(flow[v,j] for (v,j) in A) for v in I"],"objective":"maximize sum(flow[0,j] for (0,j) in A) - sum(flow[i,0] for (i,0) in A)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    adjacency = {
        0: (1, 2, 3, 4, 5, 6, 7, 8),
        1: (0, 3, 4, 5, 6, 7, 8),
        2: (0, 1, 3, 4, 5, 6, 7, 8),
        3: (0, 2, 4, 5, 6, 7, 8),
        4: (0, 1, 2, 3, 5, 6, 7, 8),
        5: (2, 3, 4, 6, 7, 8),
        6: (0, 1, 2, 3, 7, 8),
        7: (0, 1, 2, 3, 4, 5, 6, 8),
        8: (0, 1, 3, 4, 5, 6, 7),
    }
    arcs = [
        (origin, destination)
        for origin, destinations in adjacency.items()
        for destination in destinations
    ]
    capacities = {
        (origin, destination): params[f"capacity_{origin}_{destination}"]
        for origin, destination in arcs
    }
    incoming = {
        node: [(origin, destination) for origin, destination in arcs
               if destination == node]
        for node in range(9)
    }
    outgoing = {
        node: [(origin, destination) for origin, destination in arcs
               if origin == node]
        for node in range(9)
    }

    model = pyo.ConcreteModel()
    model.reservoirs = pyo.Set(initialize=range(9), ordered=True)
    model.intermediate_reservoirs = pyo.Set(
        initialize=range(1, 8), ordered=True
    )
    model.pipeline_arcs = pyo.Set(
        initialize=arcs, dimen=2, ordered=True
    )
    model.pipeline_capacity = pyo.Param(
        model.pipeline_arcs,
        initialize=capacities,
        within=pyo.Reals,
    )
    model.flow = pyo.Var(
        model.pipeline_arcs,
        domain=pyo.NonNegativeReals,
    )

    def capacity_rule(network, origin, destination):
        return (
            network.flow[origin, destination]
            <= network.pipeline_capacity[origin, destination]
        )

    model.capacity_limits = pyo.Constraint(
        model.pipeline_arcs,
        rule=capacity_rule,
    )

    def conservation_rule(network, node):
        return (
            sum(network.flow[arc] for arc in incoming[node])
            == sum(network.flow[arc] for arc in outgoing[node])
        )

    model.flow_conservation = pyo.Constraint(
        model.intermediate_reservoirs,
        rule=conservation_rule,
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
    except RuntimeError as exc:
        if "a feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_flow))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}