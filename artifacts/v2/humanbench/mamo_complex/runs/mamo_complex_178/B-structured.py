# IR: {"sets":{"cities":[0,1,2,3,4,5],"intermediate":[1,2,3,4],"arcs":[[0,1],[0,2],[0,3],[0,5],[1,0],[1,2],[1,3],[1,4],[1,5],[2,0],[2,3],[2,4],[2,5],[3,0],[3,1],[3,2],[3,4],[3,5],[4,0],[4,1],[4,2],[4,3],[4,5],[5,0],[5,1],[5,2],[5,3],[5,4]]},"params":{"capacity[i,j]":"params[f'capacity_{i}_to_{j}'] for each arc (i,j)"},"variables":{"flow[i,j]":{"type":"NonNegativeReals","indices":"arcs"}},"constraints":["flow[i,j] <= capacity[i,j] for each arc (i,j)","sum(flow[i,v] for incoming arcs) == sum(flow[v,j] for outgoing arcs) for each intermediate city v"],"objective":{"sense":"maximize","expression":"sum(flow[0,j] for outgoing source arcs) - sum(flow[i,0] for incoming source arcs)"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    arcs = (
        (0, 1), (0, 2), (0, 3), (0, 5),
        (1, 0), (1, 2), (1, 3), (1, 4), (1, 5),
        (2, 0), (2, 3), (2, 4), (2, 5),
        (3, 0), (3, 1), (3, 2), (3, 4), (3, 5),
        (4, 0), (4, 1), (4, 2), (4, 3), (4, 5),
        (5, 0), (5, 1), (5, 2), (5, 3), (5, 4),
    )

    capacities = {
        (origin, destination): params[
            f"capacity_{origin}_to_{destination}"
        ]
        for origin, destination in arcs
    }

    model = pyo.ConcreteModel()
    model.cities = pyo.Set(initialize=range(6), ordered=True)
    model.intermediate = pyo.Set(initialize=range(1, 5), ordered=True)
    model.arcs = pyo.Set(dimen=2, initialize=arcs, ordered=True)

    model.capacity = pyo.Param(
        model.arcs,
        initialize=capacities,
        within=pyo.Reals,
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

    def conservation_rule(network, city):
        incoming = sum(
            network.flow[origin, destination]
            for origin, destination in arcs
            if destination == city
        )
        outgoing = sum(
            network.flow[origin, destination]
            for origin, destination in arcs
            if origin == city
        )
        return incoming == outgoing

    model.flow_conservation = pyo.Constraint(
        model.intermediate, rule=conservation_rule
    )

    model.total_flow = pyo.Objective(
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
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_flow))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}