# IR: {"sets":{"N":[0,1,2,3,4,5],"I":[1,2,3,4],"A":[[0,1],[0,2],[0,3],[0,4],[0,5],[1,0],[1,2],[1,4],[1,5],[2,0],[2,1],[2,3],[2,4],[2,5],[3,0],[3,1],[3,2],[3,4],[3,5],[4,0],[4,1],[4,2],[4,3],[4,5],[5,0],[5,1],[5,2],[5,3],[5,4]]},"params":{"capacity[i,j]":"params[f'capacity_{i}_{j}'] for (i,j) in A"},"variables":{"flow[i,j]":"continuous, nonnegative, for (i,j) in A"},"constraints":["flow[i,j] <= capacity[i,j] for (i,j) in A","sum(flow[i,k] for (i,k) in A) == sum(flow[k,j] for (k,j) in A) for k in I"],"objective":{"sense":"maximize","expression":"sum(flow[0,j] for (0,j) in A) - sum(flow[i,0] for (i,0) in A)"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    arcs = (
        (0, 1), (0, 2), (0, 3), (0, 4), (0, 5),
        (1, 0), (1, 2), (1, 4), (1, 5),
        (2, 0), (2, 1), (2, 3), (2, 4), (2, 5),
        (3, 0), (3, 1), (3, 2), (3, 4), (3, 5),
        (4, 0), (4, 1), (4, 2), (4, 3), (4, 5),
        (5, 0), (5, 1), (5, 2), (5, 3), (5, 4),
    )

    capacities = {
        (origin, destination): params[f"capacity_{origin}_{destination}"]
        for origin, destination in arcs
    }

    model = pyo.ConcreteModel()
    model.hubs = pyo.Set(initialize=range(6))
    model.intermediate_hubs = pyo.Set(initialize=(1, 2, 3, 4))
    model.roads = pyo.Set(dimen=2, initialize=arcs)

    model.capacity = pyo.Param(model.roads, initialize=capacities)
    model.flow = pyo.Var(model.roads, domain=pyo.NonNegativeReals)

    def capacity_rule(network, origin, destination):
        return (
            network.flow[origin, destination]
            <= network.capacity[origin, destination]
        )

    model.road_limits = pyo.Constraint(
        model.roads, rule=capacity_rule
    )

    def conservation_rule(network, hub):
        incoming = sum(
            network.flow[origin, destination]
            for origin, destination in arcs
            if destination == hub
        )
        outgoing = sum(
            network.flow[origin, destination]
            for origin, destination in arcs
            if origin == hub
        )
        return incoming == outgoing

    model.flow_conservation = pyo.Constraint(
        model.intermediate_hubs, rule=conservation_rule
    )

    model.maximum_flow = pyo.Objective(
        expr=(
            sum(
                model.flow[origin, destination]
                for origin, destination in arcs
                if origin == 0
            )
            - sum(
                model.flow[origin, destination]
                for origin, destination in arcs
                if destination == 0
            )
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        # HiGHS may raise when no feasible solution can be loaded.
        # Success is determined solely by objective retrievability below.
        pass

    try:
        obj_val = float(pyo.value(model.maximum_flow))
    except (ValueError, TypeError):
        return {"objective": None, "status": "no_solution"}

    return {"objective": obj_val, "status": "optimal"}