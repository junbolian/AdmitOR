# IR: {"sets":{"N":[0,1,2,3,4,5],"A":[[0,1],[0,2],[0,5],[1,0],[1,2],[2,0],[2,1],[2,3],[3,2],[3,4],[4,1],[4,2],[4,3],[4,5],[5,0],[5,3],[5,4]],"L":[[0,1],[1,0],[1,2],[2,1],[2,3],[3,4],[4,1]]},"params":{"lower[i,j]":"params[min_flow_i_j] for (i,j) in L; otherwise 0","capacity[i,j]":"params[cap_i_j] for (i,j) in A","cost[i,j]":"params[cost_i_j] for (i,j) in A"},"variables":{"flow[i,j]":{"type":"continuous nonnegative real","indices":"(i,j) in A"}},"constraints":["flow[i,j] >= lower[i,j] for (i,j) in A","flow[i,j] <= capacity[i,j] for (i,j) in A","sum(flow[i,n] for (i,n) in A) == sum(flow[n,j] for (n,j) in A) for n in N"],"objective":{"sense":"minimize","expression":"sum(cost[i,j] * flow[i,j] for (i,j) in A)"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    arcs = (
        (0, 1), (0, 2), (0, 5),
        (1, 0), (1, 2),
        (2, 0), (2, 1), (2, 3),
        (3, 2), (3, 4),
        (4, 1), (4, 2), (4, 3), (4, 5),
        (5, 0), (5, 3), (5, 4),
    )

    mandatory_minimum = {
        (0, 1): params["min_flow_0_1"],
        (1, 0): params["min_flow_1_0"],
        (1, 2): params["min_flow_1_2"],
        (2, 1): params["min_flow_2_1"],
        (2, 3): params["min_flow_2_3"],
        (3, 4): params["min_flow_3_4"],
        (4, 1): params["min_flow_4_1"],
    }

    capacities = {
        (0, 1): params["cap_0_1"],
        (0, 2): params["cap_0_2"],
        (0, 5): params["cap_0_5"],
        (1, 0): params["cap_1_0"],
        (1, 2): params["cap_1_2"],
        (2, 0): params["cap_2_0"],
        (2, 1): params["cap_2_1"],
        (2, 3): params["cap_2_3"],
        (3, 2): params["cap_3_2"],
        (3, 4): params["cap_3_4"],
        (4, 1): params["cap_4_1"],
        (4, 2): params["cap_4_2"],
        (4, 3): params["cap_4_3"],
        (4, 5): params["cap_4_5"],
        (5, 0): params["cap_5_0"],
        (5, 3): params["cap_5_3"],
        (5, 4): params["cap_5_4"],
    }

    costs = {
        (0, 1): params["cost_0_1"],
        (0, 2): params["cost_0_2"],
        (0, 5): params["cost_0_5"],
        (1, 0): params["cost_1_0"],
        (1, 2): params["cost_1_2"],
        (2, 0): params["cost_2_0"],
        (2, 1): params["cost_2_1"],
        (2, 3): params["cost_2_3"],
        (3, 2): params["cost_3_2"],
        (3, 4): params["cost_3_4"],
        (4, 1): params["cost_4_1"],
        (4, 2): params["cost_4_2"],
        (4, 3): params["cost_4_3"],
        (4, 5): params["cost_4_5"],
        (5, 0): params["cost_5_0"],
        (5, 3): params["cost_5_3"],
        (5, 4): params["cost_5_4"],
    }

    model = pyo.ConcreteModel()
    model.nodes = pyo.Set(initialize=range(6), ordered=True)
    model.arcs = pyo.Set(dimen=2, initialize=arcs, ordered=True)

    model.lower_flow = pyo.Param(
        model.arcs,
        initialize={arc: mandatory_minimum.get(arc, 0) for arc in arcs},
        within=pyo.Reals,
    )
    model.capacity = pyo.Param(
        model.arcs, initialize=capacities, within=pyo.Reals
    )
    model.unit_cost = pyo.Param(
        model.arcs, initialize=costs, within=pyo.Reals
    )

    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    def minimum_flow_rule(network, origin, destination):
        return (
            network.flow[origin, destination]
            >= network.lower_flow[origin, destination]
        )

    def capacity_rule(network, origin, destination):
        return (
            network.flow[origin, destination]
            <= network.capacity[origin, destination]
        )

    def balance_rule(network, node):
        inflow = sum(
            network.flow[origin, destination]
            for origin, destination in arcs
            if destination == node
        )
        outflow = sum(
            network.flow[origin, destination]
            for origin, destination in arcs
            if origin == node
        )
        return inflow == outflow

    model.minimum_flow_constraints = pyo.Constraint(
        model.arcs, rule=minimum_flow_rule
    )
    model.capacity_constraints = pyo.Constraint(
        model.arcs, rule=capacity_rule
    )
    model.flow_balance = pyo.Constraint(model.nodes, rule=balance_rule)

    model.total_cost = pyo.Objective(
        expr=sum(
            model.unit_cost[origin, destination]
            * model.flow[origin, destination]
            for origin, destination in arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}