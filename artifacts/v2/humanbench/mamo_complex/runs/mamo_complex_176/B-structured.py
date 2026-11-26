# IR: {"sets":{"V":[0,1,2,3,4,5,6],"I":[1,2,3,4,5],"A":{"0":[1,2,3,4,5,6],"1":[0,2,3,4,5],"2":[0,1,3,5,6],"3":[0,1,2,4,5,6],"4":[0,1,2,3,5,6],"5":[0,1,2,3,4,6],"6":[0,1,2,3,4,5]}},"params":{"capacity[i,j]":"params['cap_i_j'] for (i,j) in A; directed capacities"},"variables":{"flow[i,j]":"NonNegativeReals for (i,j) in A"},"constraints":["flow[i,j] <= capacity[i,j] for (i,j) in A","sum(flow[i,v] for (i,v) in A) = sum(flow[v,j] for (v,j) in A) for v in I"],"objective":{"sense":"maximize","expression":"sum(flow[0,j] for (0,j) in A) - sum(flow[i,0] for (i,0) in A)"}}

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
        (1, 2): params["cap_1_2"],
        (1, 3): params["cap_1_3"],
        (1, 4): params["cap_1_4"],
        (1, 5): params["cap_1_5"],
        (2, 0): params["cap_2_0"],
        (2, 1): params["cap_2_1"],
        (2, 3): params["cap_2_3"],
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
        (5, 1): params["cap_5_1"],
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
    model.V = pyo.Set(initialize=range(7))
    model.I = pyo.Set(initialize=range(1, 6))
    model.A = pyo.Set(dimen=2, initialize=capacities.keys())
    model.capacity = pyo.Param(
        model.A, initialize=capacities, within=pyo.Reals
    )
    model.flow = pyo.Var(model.A, domain=pyo.NonNegativeReals)

    def capacity_rule(network, origin, destination):
        return (
            network.flow[origin, destination]
            <= network.capacity[origin, destination]
        )

    model.capacity_limit = pyo.Constraint(model.A, rule=capacity_rule)

    def conservation_rule(network, city):
        return (
            sum(
                network.flow[origin, destination]
                for origin, destination in network.A
                if destination == city
            )
            == sum(
                network.flow[origin, destination]
                for origin, destination in network.A
                if origin == city
            )
        )

    model.flow_balance = pyo.Constraint(
        model.I, rule=conservation_rule
    )

    model.total_flow = pyo.Objective(
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
    except RuntimeError as exc:
        # APPsi raises this when automatic solution loading finds no solution.
        # Objective retrieval below remains the sole success criterion.
        if "a feasible solution was not found" not in str(exc).lower():
            raise

    try:
        obj_val = float(pyo.value(model.total_flow))
    except ValueError:
        return {"objective": None, "status": "no_solution"}

    return {"objective": obj_val, "status": "optimal"}