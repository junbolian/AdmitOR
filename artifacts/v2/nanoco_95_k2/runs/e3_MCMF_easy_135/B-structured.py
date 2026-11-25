# IR: {"sets":{"N":[0,1,2,3,4,5,6,7,8],"A":[[0,1],[0,2],[0,6],[0,8],[1,2],[1,5],[2,3],[2,6],[3,4],[4,5],[5,6],[6,7],[6,8],[7,8]]},"params":{"capacity[i,j]":"params['cap_i_j'] for (i,j) in A; nonnegative","cost[i,j]":"params['cost_i_j'] for (i,j) in A; real","node_coords":"params['node_coords']; geometry only"},"variables":{"flow[i,j]":"continuous nonnegative for (i,j) in A","throughput":"continuous nonnegative"},"constraints":["flow[i,j] <= capacity[i,j] for (i,j) in A","sum(flow[i,j] for outgoing arcs) - sum(flow[j,i] for incoming arcs) = throughput at node 0, -throughput at node 8, and 0 otherwise","Stage 2 only: throughput = optimal Stage 1 throughput"],"objective":{"priority_1":"maximize throughput","priority_2":"minimize sum(cost[i,j]*flow[i,j] for (i,j) in A) with throughput fixed at its Stage 1 optimum","returned_objective":"optimal Stage 2 total transmission cost"}}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    arcs = (
        (0, 1), (0, 2), (0, 6), (0, 8),
        (1, 2), (1, 5),
        (2, 3), (2, 6),
        (3, 4),
        (4, 5),
        (5, 6),
        (6, 7), (6, 8),
        (7, 8),
    )

    capacities = {
        (0, 1): params["cap_0_1"],
        (0, 2): params["cap_0_2"],
        (0, 6): params["cap_0_6"],
        (0, 8): params["cap_0_8"],
        (1, 2): params["cap_1_2"],
        (1, 5): params["cap_1_5"],
        (2, 3): params["cap_2_3"],
        (2, 6): params["cap_2_6"],
        (3, 4): params["cap_3_4"],
        (4, 5): params["cap_4_5"],
        (5, 6): params["cap_5_6"],
        (6, 7): params["cap_6_7"],
        (6, 8): params["cap_6_8"],
        (7, 8): params["cap_7_8"],
    }

    costs = {
        (0, 1): params["cost_0_1"],
        (0, 2): params["cost_0_2"],
        (0, 6): params["cost_0_6"],
        (0, 8): params["cost_0_8"],
        (1, 2): params["cost_1_2"],
        (1, 5): params["cost_1_5"],
        (2, 3): params["cost_2_3"],
        (2, 6): params["cost_2_6"],
        (3, 4): params["cost_3_4"],
        (4, 5): params["cost_4_5"],
        (5, 6): params["cost_5_6"],
        (6, 7): params["cost_6_7"],
        (6, 8): params["cost_6_8"],
        (7, 8): params["cost_7_8"],
    }

    node_coords = params["node_coords"]  # Geometry is not an optimization coefficient.

    model = pyo.ConcreteModel()
    model.nodes = pyo.Set(initialize=range(9), ordered=True)
    model.arcs = pyo.Set(dimen=2, initialize=arcs, ordered=True)

    model.capacity = pyo.Param(
        model.arcs, initialize=capacities, within=pyo.NonNegativeReals
    )
    model.unit_cost = pyo.Param(
        model.arcs, initialize=costs, within=pyo.Reals
    )

    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)
    model.throughput = pyo.Var(domain=pyo.NonNegativeReals)

    def capacity_rule(network, origin, destination):
        return (
            network.flow[origin, destination]
            <= network.capacity[origin, destination]
        )

    model.arc_limits = pyo.Constraint(model.arcs, rule=capacity_rule)

    def balance_rule(network, node):
        outgoing = sum(
            network.flow[origin, destination]
            for origin, destination in arcs
            if origin == node
        )
        incoming = sum(
            network.flow[origin, destination]
            for origin, destination in arcs
            if destination == node
        )
        if node == 0:
            return outgoing - incoming == network.throughput
        if node == 8:
            return outgoing - incoming == -network.throughput
        return outgoing - incoming == 0

    model.flow_balance = pyo.Constraint(model.nodes, rule=balance_rule)

    model.max_throughput = pyo.Objective(
        expr=model.throughput, sense=pyo.maximize
    )

    # First priority: maximize source-to-destination throughput.
    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        maximum_throughput = float(pyo.value(model.max_throughput))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    # Second priority: minimize cost while preserving maximum throughput.
    model.fixed_throughput = pyo.Constraint(
        expr=model.throughput == maximum_throughput
    )
    model.max_throughput.deactivate()
    model.min_cost = pyo.Objective(
        expr=sum(
            model.unit_cost[origin, destination]
            * model.flow[origin, destination]
            for origin, destination in arcs
        ),
        sense=pyo.minimize,
    )

    # Remove Stage 1 variable values so failed loading cannot leave a stale
    # objective available for the Stage 2 success check.
    for origin, destination in arcs:
        model.flow[origin, destination].set_value(None)
    model.throughput.set_value(None)

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.min_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}