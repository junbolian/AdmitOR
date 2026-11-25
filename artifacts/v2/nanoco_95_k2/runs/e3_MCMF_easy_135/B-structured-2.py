# IR: {"sets":{"N":[0,1,2,3,4,5,6,7,8],"A":[[0,1],[0,2],[0,6],[0,8],[1,2],[1,5],[2,3],[2,6],[3,4],[4,5],[5,6],[6,7],[6,8],[7,8]]},"params":{"capacity[i,j]":"params['cap_i_j'] for every (i,j) in A","cost[i,j]":"params['cost_i_j'] for every (i,j) in A","node_coords":"params['node_coords']; geometry only"},"variables":{"flow[i,j]":"NonNegativeReals for (i,j) in A","throughput":"NonNegativeReals"},"constraints":["flow[i,j] <= capacity[i,j] for every (i,j) in A","outflow[n] - inflow[n] = throughput if n=0, -throughput if n=8, otherwise 0","Stage 2: fix throughput to the objective value retrieved after Stage 1"],"objective":{"Stage 1":"maximize throughput","Stage 2":"minimize sum(cost[i,j]*flow[i,j] for (i,j) in A)","returned_objective":"Stage 2 minimum transmission cost at maximum throughput"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
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
    nodes = tuple(range(9))

    capacities = {
        (tail, head): params[f"cap_{tail}_{head}"]
        for tail, head in arcs
    }
    costs = {
        (tail, head): params[f"cost_{tail}_{head}"]
        for tail, head in arcs
    }
    node_coords = params["node_coords"]  # Geometry does not affect optimization.

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
    model.arcs = pyo.Set(dimen=2, initialize=arcs, ordered=True)

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

    model.capacity_limits = pyo.Constraint(
        model.arcs, rule=capacity_rule
    )

    def balance_rule(network, node):
        net_outflow = (
            sum(network.flow[arc] for arc in outgoing[node])
            - sum(network.flow[arc] for arc in incoming[node])
        )
        if node == 0:
            return net_outflow == network.throughput
        if node == 8:
            return net_outflow == -network.throughput
        return net_outflow == 0

    model.flow_balance = pyo.Constraint(
        model.nodes, rule=balance_rule
    )

    model.throughput_objective = pyo.Objective(
        expr=model.throughput,
        sense=pyo.maximize,
    )
    model.cost_objective = pyo.Objective(
        expr=sum(
            model.unit_cost[tail, head] * model.flow[tail, head]
            for tail, head in model.arcs
        ),
        sense=pyo.minimize,
    )
    model.cost_objective.deactivate()

    # Stage 1: maximize throughput.
    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.throughput_objective))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    # Stage 2: minimize cost while preserving maximum throughput.
    model.throughput.fix(obj_val)
    model.throughput_objective.deactivate()
    model.cost_objective.activate()

    # Remove previous flow values so a missing second-stage solution
    # cannot be mistaken for a retrievable second-stage objective.
    for arc in arcs:
        model.flow[arc].set_value(None)

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.cost_objective))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}