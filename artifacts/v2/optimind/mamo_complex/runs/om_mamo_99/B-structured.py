# IR: {"sets":{"N":[0,1,2,3,4,5],"I":[1,2,3,4],"A":"{(i,j) in N x N: i != j and (i,j) != (1,3)}"},"params":{"capacity[i,j]":"params['capacity_<i>_<j>'] for every (i,j) in A"},"variables":{"flow[i,j]":"NonNegativeReals for every (i,j) in A"},"constraints":["flow[i,j] <= capacity[i,j] for every (i,j) in A","sum(flow[i,k] for (i,k) in A) = sum(flow[k,j] for (k,j) in A) for every k in I"],"objective":"maximize sum(flow[0,j] for (0,j) in A) - sum(flow[i,0] for (i,0) in A)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    capacity_data = {
        (0, 1): params["capacity_0_1"],
        (0, 2): params["capacity_0_2"],
        (0, 3): params["capacity_0_3"],
        (0, 4): params["capacity_0_4"],
        (0, 5): params["capacity_0_5"],
        (1, 0): params["capacity_1_0"],
        (1, 2): params["capacity_1_2"],
        (1, 4): params["capacity_1_4"],
        (1, 5): params["capacity_1_5"],
        (2, 0): params["capacity_2_0"],
        (2, 1): params["capacity_2_1"],
        (2, 3): params["capacity_2_3"],
        (2, 4): params["capacity_2_4"],
        (2, 5): params["capacity_2_5"],
        (3, 0): params["capacity_3_0"],
        (3, 1): params["capacity_3_1"],
        (3, 2): params["capacity_3_2"],
        (3, 4): params["capacity_3_4"],
        (3, 5): params["capacity_3_5"],
        (4, 0): params["capacity_4_0"],
        (4, 1): params["capacity_4_1"],
        (4, 2): params["capacity_4_2"],
        (4, 3): params["capacity_4_3"],
        (4, 5): params["capacity_4_5"],
        (5, 0): params["capacity_5_0"],
        (5, 1): params["capacity_5_1"],
        (5, 2): params["capacity_5_2"],
        (5, 3): params["capacity_5_3"],
        (5, 4): params["capacity_5_4"],
    }

    model = pyo.ConcreteModel()
    model.N = pyo.RangeSet(0, 5)
    model.I = pyo.RangeSet(1, 4)
    model.A = pyo.Set(
        dimen=2,
        within=model.N * model.N,
        initialize=capacity_data.keys(),
    )
    model.capacity = pyo.Param(
        model.A,
        initialize=capacity_data,
        within=pyo.NonNegativeReals,
    )
    model.flow = pyo.Var(model.A, domain=pyo.NonNegativeReals)

    def capacity_rule(network, origin, destination):
        return (
            network.flow[origin, destination]
            <= network.capacity[origin, destination]
        )

    model.road_capacity = pyo.Constraint(model.A, rule=capacity_rule)

    def conservation_rule(network, hub):
        incoming = sum(
            network.flow[origin, destination]
            for origin, destination in network.A
            if destination == hub
        )
        outgoing = sum(
            network.flow[origin, destination]
            for origin, destination in network.A
            if origin == hub
        )
        return incoming == outgoing

    model.flow_conservation = pyo.Constraint(
        model.I,
        rule=conservation_rule,
    )

    model.total_delivery = pyo.Objective(
        expr=(
            sum(
                model.flow[origin, destination]
                for origin, destination in model.A
                if origin == 0
            )
            - sum(
                model.flow[origin, destination]
                for origin, destination in model.A
                if destination == 0
            )
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_delivery))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}