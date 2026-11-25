# IR: {"sets":{"N":"0..num_nodes-1","A":[[0,1],[0,2],[0,6],[0,8],[1,2],[1,5],[2,3],[2,6],[3,4],[4,5],[5,6],[6,7],[6,8],[7,8]]},"params":{"capacity[i,j]":"params['capacity_i_j'] for (i,j) in A","cost[i,j]":"params['cost_i_j'] for (i,j) in A","node_coords_x":"params['node_coords_x']; metadata only","node_coords_y":"params['node_coords_y']; metadata only","num_nodes":"params['num_nodes']; must equal 9","num_arcs":"params['num_arcs']; must equal |A|"},"variables":{"flow[i,j]":"NonNegativeReals","throughput":"NonNegativeReals"},"constraints":["flow[i,j] <= capacity[i,j] for every arc","outflow[n]-inflow[n] = throughput if n=0, -throughput if n=8, otherwise 0","stage 2 only: throughput = optimal stage-1 throughput"],"objective":{"stage_1":"maximize throughput","stage_2":"minimize sum(cost[i,j]*flow[i,j] for (i,j) in A)","returned_objective":"minimum total transmission cost at maximum throughput"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Return the minimum transmission cost among maximum-throughput routings."""
    arcs = (
        (0, 1),
        (0, 2),
        (0, 6),
        (0, 8),
        (1, 2),
        (1, 5),
        (2, 3),
        (2, 6),
        (3, 4),
        (4, 5),
        (5, 6),
        (6, 7),
        (6, 8),
        (7, 8),
    )

    num_nodes = params["num_nodes"]
    num_arcs = params["num_arcs"]
    node_coords_x = params["node_coords_x"]
    node_coords_y = params["node_coords_y"]

    capacities = {
        (0, 1): params["capacity_0_1"],
        (0, 2): params["capacity_0_2"],
        (0, 6): params["capacity_0_6"],
        (0, 8): params["capacity_0_8"],
        (1, 2): params["capacity_1_2"],
        (1, 5): params["capacity_1_5"],
        (2, 3): params["capacity_2_3"],
        (2, 6): params["capacity_2_6"],
        (3, 4): params["capacity_3_4"],
        (4, 5): params["capacity_4_5"],
        (5, 6): params["capacity_5_6"],
        (6, 7): params["capacity_6_7"],
        (6, 8): params["capacity_6_8"],
        (7, 8): params["capacity_7_8"],
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

    if num_nodes != 9 or num_arcs != len(arcs):
        return {"objective": None, "status": "invalid_topology"}

    model = pyo.ConcreteModel()
    model.node_count = pyo.Param(initialize=num_nodes, within=pyo.PositiveIntegers)
    model.arc_count = pyo.Param(initialize=num_arcs, within=pyo.PositiveIntegers)
    model.nodes = pyo.RangeSet(0, int(num_nodes) - 1)
    model.arcs = pyo.Set(dimen=2, initialize=arcs, ordered=True)

    model.capacity = pyo.Param(
        model.arcs, initialize=capacities, within=pyo.NonNegativeReals
    )
    model.unit_cost = pyo.Param(
        model.arcs, initialize=costs, within=pyo.Reals
    )
    model.coord_x = pyo.Param(
        model.nodes,
        initialize={node: node_coords_x[node] for node in range(int(num_nodes))},
        within=pyo.Reals,
    )
    model.coord_y = pyo.Param(
        model.nodes,
        initialize={node: node_coords_y[node] for node in range(int(num_nodes))},
        within=pyo.Reals,
    )

    model.flow = pyo.Var(model.arcs, within=pyo.NonNegativeReals)
    model.throughput = pyo.Var(within=pyo.NonNegativeReals)

    def capacity_rule(network, tail, head):
        return network.flow[tail, head] <= network.capacity[tail, head]

    model.capacity_limits = pyo.Constraint(model.arcs, rule=capacity_rule)

    def balance_rule(network, node):
        outflow = sum(
            network.flow[tail, head] for tail, head in arcs if tail == node
        )
        inflow = sum(
            network.flow[tail, head] for tail, head in arcs if head == node
        )
        if node == 0:
            return outflow - inflow == network.throughput
        if node == 8:
            return outflow - inflow == -network.throughput
        return outflow - inflow == 0

    model.flow_balance = pyo.Constraint(model.nodes, rule=balance_rule)

    model.throughput_objective = pyo.Objective(
        expr=model.throughput, sense=pyo.maximize
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "stage_1_solve_failed"}

    try:
        obj_val = float(pyo.value(model.throughput_objective))
    except (ValueError, TypeError):
        return {"objective": None, "status": "stage_1_no_objective"}

    maximum_throughput = obj_val
    model.throughput_objective.deactivate()
    model.maximum_throughput_requirement = pyo.Constraint(
        expr=model.throughput == maximum_throughput
    )
    model.cost_objective = pyo.Objective(
        expr=sum(
            model.unit_cost[tail, head] * model.flow[tail, head]
            for tail, head in arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "stage_2_solve_failed"}

    try:
        obj_val = float(pyo.value(model.cost_objective))
    except (ValueError, TypeError):
        return {"objective": None, "status": "stage_2_no_objective"}

    return {"objective": obj_val, "status": "optimal"}