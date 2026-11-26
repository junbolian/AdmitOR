# IR: {"sets":{"V":[0,1,2,3,4,5,6,7],"A":{"0":[1,2,3,5,6,7],"1":[0,2,3,4,5,6],"2":[0,1,3,4,5,6,7],"3":[0,1,2,4,5,7],"4":[0,1,2,3,5,6,7],"5":[0,1,2,3,4,6,7],"6":[0,1,2,3,4,5,7],"7":[0,1,3,4,5,6]}},"params":{"capacity[i,j]":"params['capacity_'+str(i)+'_'+str(j)] for (i,j) in A; nonnegative real"},"variables":{"flow[i,j]":"nonnegative continuous real for (i,j) in A"},"constraints":["flow[i,j] <= capacity[i,j] for every (i,j) in A","sum(flow[i,v] for incoming arcs) = sum(flow[v,j] for outgoing arcs) for v in V excluding 0 and 7"],"objective":"maximize sum(flow[0,j] for outgoing source arcs) - sum(flow[i,0] for incoming source arcs)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    adjacency = {
        0: (1, 2, 3, 5, 6, 7),
        1: (0, 2, 3, 4, 5, 6),
        2: (0, 1, 3, 4, 5, 6, 7),
        3: (0, 1, 2, 4, 5, 7),
        4: (0, 1, 2, 3, 5, 6, 7),
        5: (0, 1, 2, 3, 4, 6, 7),
        6: (0, 1, 2, 3, 4, 5, 7),
        7: (0, 1, 3, 4, 5, 6),
    }
    arcs = [
        (tail, head)
        for tail, destinations in adjacency.items()
        for head in destinations
    ]
    capacities = {
        (tail, head): params[f"capacity_{tail}_{head}"]
        for tail, head in arcs
    }
    incoming = {
        hub: [(tail, head) for tail, head in arcs if head == hub]
        for hub in range(8)
    }
    outgoing = {
        hub: [(tail, head) for tail, head in arcs if tail == hub]
        for hub in range(8)
    }

    model = pyo.ConcreteModel()
    model.hubs = pyo.Set(initialize=range(8), ordered=True)
    model.arcs = pyo.Set(dimen=2, initialize=arcs, ordered=True)
    model.transit_hubs = pyo.Set(
        initialize=[hub for hub in range(8) if hub not in (0, 7)],
        ordered=True,
    )
    model.capacity = pyo.Param(
        model.arcs,
        initialize=capacities,
        within=pyo.NonNegativeReals,
    )
    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    def capacity_rule(current_model, tail, head):
        return (
            current_model.flow[tail, head]
            <= current_model.capacity[tail, head]
        )

    model.capacity_limits = pyo.Constraint(
        model.arcs,
        rule=capacity_rule,
    )

    def conservation_rule(current_model, hub):
        return (
            sum(current_model.flow[arc] for arc in incoming[hub])
            == sum(current_model.flow[arc] for arc in outgoing[hub])
        )

    model.flow_conservation = pyo.Constraint(
        model.transit_hubs,
        rule=conservation_rule,
    )
    model.max_flow_objective = pyo.Objective(
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
        obj_val = float(pyo.value(model.max_flow_objective))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}