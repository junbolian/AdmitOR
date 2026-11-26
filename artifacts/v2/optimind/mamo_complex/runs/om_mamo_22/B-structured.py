# IR: {"sets":{"H":[0,1,2,3,4,5,6],"T":[1,2,3,4,5],"A":[[0,1],[0,2],[0,3],[0,4],[0,5],[0,6],[1,0],[1,4],[1,5],[1,6],[2,0],[2,1],[2,3],[2,4],[2,5],[2,6],[3,0],[3,1],[3,2],[3,4],[3,5],[3,6],[4,0],[4,1],[4,2],[4,3],[4,5],[4,6],[5,0],[5,2],[5,3],[5,4],[5,6],[6,0],[6,1],[6,2],[6,3],[6,4],[6,5]]},"params":{"cap[i,j]":"params['cap_i_j'] for every (i,j) in A"},"variables":{"flow[i,j]":{"type":"continuous","lower_bound":0,"index":"A"}},"constraints":["flow[i,j] <= cap[i,j] for every (i,j) in A","sum(flow[i,h] for (i,h) in A) = sum(flow[h,j] for (h,j) in A) for every h in T"],"objective":{"sense":"maximize","expression":"sum(flow[0,j] for (0,j) in A) - sum(flow[i,0] for (i,0) in A)"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    capacities = {
        (0, 1): params["cap_0_1"],
        (0, 2): params["cap_0_2"],
        (0, 3): params["cap_0_3"],
        (0, 4): params["cap_0_4"],
        (0, 5): params["cap_0_5"],
        (0, 6): params["cap_0_6"],
        (1, 0): params["cap_1_0"],
        (1, 4): params["cap_1_4"],
        (1, 5): params["cap_1_5"],
        (1, 6): params["cap_1_6"],
        (2, 0): params["cap_2_0"],
        (2, 1): params["cap_2_1"],
        (2, 3): params["cap_2_3"],
        (2, 4): params["cap_2_4"],
        (2, 5): params["cap_2_5"],
        (2, 6): params["cap_2_6"],
        (3, 0): params["cap_3_0"],
        (3, 1): params["cap_3_1"],
        (3, 2): params["cap_3_2"],
        (3, 4): params["cap_3_4"],
        (3, 5): params["cap_3_5"],
        (3, 6): params["cap_3_6"],
        (4, 0): params["cap_4_0"],
        (4, 1): params["cap_4_1"],
        (4, 2): params["cap_4_2"],
        (4, 3): params["cap_4_3"],
        (4, 5): params["cap_4_5"],
        (4, 6): params["cap_4_6"],
        (5, 0): params["cap_5_0"],
        (5, 2): params["cap_5_2"],
        (5, 3): params["cap_5_3"],
        (5, 4): params["cap_5_4"],
        (5, 6): params["cap_5_6"],
        (6, 0): params["cap_6_0"],
        (6, 1): params["cap_6_1"],
        (6, 2): params["cap_6_2"],
        (6, 3): params["cap_6_3"],
        (6, 4): params["cap_6_4"],
        (6, 5): params["cap_6_5"],
    }

    model = pyo.ConcreteModel()
    model.hubs = pyo.RangeSet(0, 6)
    model.transit_hubs = pyo.RangeSet(1, 5)
    model.arcs = pyo.Set(dimen=2, initialize=list(capacities))
    model.capacity = pyo.Param(
        model.arcs, initialize=capacities, within=pyo.Reals
    )
    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    incoming = {
        hub: [(origin, destination) for origin, destination in capacities
              if destination == hub]
        for hub in model.hubs
    }
    outgoing = {
        hub: [(origin, destination) for origin, destination in capacities
              if origin == hub]
        for hub in model.hubs
    }

    def capacity_rule(network, origin, destination):
        return (
            network.flow[origin, destination]
            <= network.capacity[origin, destination]
        )

    model.lane_limits = pyo.Constraint(model.arcs, rule=capacity_rule)

    def conservation_rule(network, hub):
        return (
            pyo.quicksum(network.flow[arc] for arc in incoming[hub])
            == pyo.quicksum(network.flow[arc] for arc in outgoing[hub])
        )

    model.flow_balance = pyo.Constraint(
        model.transit_hubs, rule=conservation_rule
    )

    model.total_dispatch = pyo.Objective(
        expr=(
            pyo.quicksum(model.flow[arc] for arc in outgoing[0])
            - pyo.quicksum(model.flow[arc] for arc in incoming[0])
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "infeasible_or_failed"}

    try:
        obj_val = float(pyo.value(model.total_dispatch))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}