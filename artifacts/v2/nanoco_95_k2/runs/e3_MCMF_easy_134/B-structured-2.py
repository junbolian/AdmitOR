# IR: {"sets":{"nodes":"0..9","arcs":[[0,1],[1,2],[1,4],[1,5],[1,7],[2,3],[3,4],[4,5],[4,8],[4,9],[5,6],[5,7],[6,7],[7,8],[8,9]]},"params":{"capacity[i,j]":"params['capacity_i_j'], nonnegative real, for each arc","cost[i,j]":"params['cost_i_j'], real, for each arc"},"variables":{"flow[i,j]":"nonnegative continuous, for each arc","throughput":"nonnegative continuous"},"constraints":["flow[i,j] <= capacity[i,j] for each arc","outflow[v] - inflow[v] = throughput if v=0, -throughput if v=9, else 0","stage 2 only: throughput = optimal stage-1 throughput"],"objective":{"priority_1":"maximize throughput","priority_2":"fix optimal throughput, then minimize sum(cost[i,j]*flow[i,j]); return this minimum cost"}}

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
        (tail, head): params[f"capacity_{tail}_{head}"]
        for tail, head in arcs
    }
    costs = {
        (tail, head): params[f"cost_{tail}_{head}"]
        for tail, head in arcs
    }

    outgoing = {
        node: tuple(arc for arc in arcs if arc[0] == node)
        for node in range(10)
    }
    incoming = {
        node: tuple(arc for arc in arcs if arc[1] == node)
        for node in range(10)
    }

    model = pyo.ConcreteModel()
    model.nodes = pyo.RangeSet(0, 9)
    model.arcs = pyo.Set(dimen=2, initialize=arcs, ordered=True)

    model.pipe_capacity = pyo.Param(
        model.arcs,
        initialize=capacities,
        within=pyo.NonNegativeReals,
    )
    model.unit_cost = pyo.Param(
        model.arcs,
        initialize=costs,
        within=pyo.Reals,
    )

    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)
    model.throughput = pyo.Var(domain=pyo.NonNegativeReals)

    def capacity_rule(network, tail, head):
        return (
            network.flow[tail, head]
            <= network.pipe_capacity[tail, head]
        )

    model.capacity_limits = pyo.Constraint(
        model.arcs,
        rule=capacity_rule,
    )

    def balance_rule(network, node):
        net_outflow = (
            pyo.quicksum(network.flow[arc] for arc in outgoing[node])
            - pyo.quicksum(network.flow[arc] for arc in incoming[node])
        )
        if node == 0:
            return net_outflow == network.throughput
        if node == 9:
            return net_outflow == -network.throughput
        return net_outflow == 0

    model.flow_balance = pyo.Constraint(
        model.nodes,
        rule=balance_rule,
    )

    model.maximum_flow = pyo.Objective(
        expr=model.throughput,
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "max_flow_solve_failed"}

    try:
        obj_val = float(pyo.value(model.maximum_flow))
    except (ValueError, TypeError):
        return {"objective": None, "status": "max_flow_unavailable"}

    maximum_throughput = obj_val

    model.maximum_flow.deactivate()
    model.fixed_throughput = pyo.Constraint(
        expr=model.throughput == maximum_throughput
    )
    model.minimum_cost = pyo.Objective(
        expr=pyo.quicksum(
            model.unit_cost[tail, head] * model.flow[tail, head]
            for tail, head in model.arcs
        ),
        sense=pyo.minimize,
    )

    # Clear the previous solution so an unavailable second-stage solution
    # cannot be mistaken for a successfully loaded solution.
    for tail, head in arcs:
        model.flow[tail, head].set_value(None)
    model.throughput.set_value(None)

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "min_cost_solve_failed"}

    try:
        obj_val = float(pyo.value(model.minimum_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "min_cost_unavailable"}

    return {"objective": obj_val, "status": "optimal"}