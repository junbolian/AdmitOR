# IR: {"sets":{"N":[0,1,2,3,4,5,6,7,8,9],"A":[[0,1],[1,2],[1,4],[1,5],[1,7],[2,3],[3,4],[4,5],[4,8],[4,9],[5,6],[5,7],[6,7],[7,8],[8,9]]},"params":{"capacity[i,j]":"params['capacity_i_j'] for every arc (i,j)","cost[i,j]":"params['cost_i_j'] for every arc (i,j)"},"variables":{"flow[i,j]":"continuous nonnegative for every arc","throughput":"continuous nonnegative"},"constraints":["flow[i,j] <= capacity[i,j] for every arc","sum_j flow[v,j] - sum_i flow[i,v] = throughput if v=0, -throughput if v=9, otherwise 0, for every node v","stage 2 only: throughput = optimal stage-1 throughput"],"objective":{"priority_1":"maximize throughput","priority_2":"fix optimal throughput, then minimize sum_(i,j) cost[i,j]*flow[i,j]","returned_objective":"minimum total operational cost at maximum throughput"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    arcs = (
        (0, 1),
        (1, 2),
        (1, 4),
        (1, 5),
        (1, 7),
        (2, 3),
        (3, 4),
        (4, 5),
        (4, 8),
        (4, 9),
        (5, 6),
        (5, 7),
        (6, 7),
        (7, 8),
        (8, 9),
    )

    capacities = {
        (0, 1): params["capacity_0_1"],
        (1, 2): params["capacity_1_2"],
        (1, 4): params["capacity_1_4"],
        (1, 5): params["capacity_1_5"],
        (1, 7): params["capacity_1_7"],
        (2, 3): params["capacity_2_3"],
        (3, 4): params["capacity_3_4"],
        (4, 5): params["capacity_4_5"],
        (4, 8): params["capacity_4_8"],
        (4, 9): params["capacity_4_9"],
        (5, 6): params["capacity_5_6"],
        (5, 7): params["capacity_5_7"],
        (6, 7): params["capacity_6_7"],
        (7, 8): params["capacity_7_8"],
        (8, 9): params["capacity_8_9"],
    }

    costs = {
        (0, 1): params["cost_0_1"],
        (1, 2): params["cost_1_2"],
        (1, 4): params["cost_1_4"],
        (1, 5): params["cost_1_5"],
        (1, 7): params["cost_1_7"],
        (2, 3): params["cost_2_3"],
        (3, 4): params["cost_3_4"],
        (4, 5): params["cost_4_5"],
        (4, 8): params["cost_4_8"],
        (4, 9): params["cost_4_9"],
        (5, 6): params["cost_5_6"],
        (5, 7): params["cost_5_7"],
        (6, 7): params["cost_6_7"],
        (7, 8): params["cost_7_8"],
        (8, 9): params["cost_8_9"],
    }

    nodes = tuple(range(10))
    outgoing = {
        node: tuple(arc for arc in arcs if arc[0] == node)
        for node in nodes
    }
    incoming = {
        node: tuple(arc for arc in arcs if arc[1] == node)
        for node in nodes
    }

    model = pyo.ConcreteModel()
    model.nodes = pyo.Set(initialize=nodes, ordered=True)
    model.arcs = pyo.Set(initialize=arcs, dimen=2, ordered=True)

    model.capacity = pyo.Param(
        model.arcs, initialize=capacities, within=pyo.Reals
    )
    model.unit_cost = pyo.Param(
        model.arcs, initialize=costs, within=pyo.Reals
    )

    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)
    model.throughput = pyo.Var(domain=pyo.NonNegativeReals)

    def capacity_rule(network, tail, head):
        return network.flow[tail, head] <= network.capacity[tail, head]

    model.pipe_limits = pyo.Constraint(model.arcs, rule=capacity_rule)

    def balance_rule(network, node):
        net_outflow = (
            sum(network.flow[arc] for arc in outgoing[node])
            - sum(network.flow[arc] for arc in incoming[node])
        )
        if node == 0:
            return net_outflow == network.throughput
        if node == 9:
            return net_outflow == -network.throughput
        return net_outflow == 0

    model.flow_balance = pyo.Constraint(model.nodes, rule=balance_rule)

    model.max_flow_objective = pyo.Objective(
        expr=model.throughput,
        sense=pyo.maximize,
    )

    # Stage 1: maximize source-to-sink throughput.
    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "stage1_solve_failed"}

    try:
        max_throughput = float(pyo.value(model.max_flow_objective))
    except ValueError:
        return {"objective": None, "status": "stage1_no_objective"}

    # Stage 2: preserve maximum throughput and minimize operational cost.
    model.max_flow_objective.deactivate()
    model.maximum_throughput_lock = pyo.Constraint(
        expr=model.throughput == max_throughput
    )
    model.min_cost_objective = pyo.Objective(
        expr=sum(
            model.unit_cost[tail, head] * model.flow[tail, head]
            for tail, head in model.arcs
        ),
        sense=pyo.minimize,
    )

    # Remove stage-1 variable values so they cannot masquerade as a
    # retrievable stage-2 objective if no new solution is loaded.
    for variable in model.component_data_objects(pyo.Var):
        variable.set_value(None)

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "stage2_solve_failed"}

    try:
        obj_val = float(pyo.value(model.min_cost_objective))
    except ValueError:
        return {"objective": None, "status": "stage2_no_objective"}

    return {"objective": obj_val, "status": "optimal"}