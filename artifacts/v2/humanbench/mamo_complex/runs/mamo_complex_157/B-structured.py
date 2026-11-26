# IR: {"sets":{"nodes":[0,1,2,3,4,5,6],"arcs":[[0,1],[0,2],[0,3],[0,4],[0,6],[1,0],[1,2],[1,3],[1,4],[1,5],[1,6],[2,0],[2,1],[2,3],[2,4],[2,5],[3,0],[3,1],[3,4],[3,5],[3,6],[4,0],[4,1],[4,2],[4,3],[4,5],[4,6],[5,0],[5,1],[5,2],[5,3],[5,4],[5,6],[6,0],[6,1],[6,2],[6,3],[6,4],[6,5]]},"params":{"capacity[i,j]":"params['capacity_i_j'] for each (i,j) in arcs"},"variables":{"flow[i,j]":"nonnegative continuous for each arc","throughput":"nonnegative continuous"},"constraints":["flow[i,j] <= capacity[i,j] for each arc","sum(outgoing flow) - sum(incoming flow) = throughput at node 0, -throughput at node 6, and 0 at every other node"],"objective":"maximize throughput"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    arcs = (
        (0, 1), (0, 2), (0, 3), (0, 4), (0, 6),
        (1, 0), (1, 2), (1, 3), (1, 4), (1, 5), (1, 6),
        (2, 0), (2, 1), (2, 3), (2, 4), (2, 5),
        (3, 0), (3, 1), (3, 4), (3, 5), (3, 6),
        (4, 0), (4, 1), (4, 2), (4, 3), (4, 5), (4, 6),
        (5, 0), (5, 1), (5, 2), (5, 3), (5, 4), (5, 6),
        (6, 0), (6, 1), (6, 2), (6, 3), (6, 4), (6, 5),
    )

    capacities = {
        (tail, head): params[f"capacity_{tail}_{head}"]
        for tail, head in arcs
    }
    outgoing = {
        node: tuple(head for tail, head in arcs if tail == node)
        for node in range(7)
    }
    incoming = {
        node: tuple(tail for tail, head in arcs if head == node)
        for node in range(7)
    }

    model = pyo.ConcreteModel()
    model.nodes = pyo.Set(initialize=range(7), ordered=True)
    model.arcs = pyo.Set(initialize=arcs, dimen=2, ordered=True)
    model.capacity = pyo.Param(
        model.arcs,
        initialize=capacities,
        within=pyo.Reals,
    )
    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)
    model.throughput = pyo.Var(domain=pyo.NonNegativeReals)

    def capacity_rule(network, tail, head):
        return network.flow[tail, head] <= network.capacity[tail, head]

    model.capacity_limit = pyo.Constraint(
        model.arcs,
        rule=capacity_rule,
    )

    def balance_rule(network, node):
        net_outflow = (
            sum(network.flow[node, head] for head in outgoing[node])
            - sum(network.flow[tail, node] for tail in incoming[node])
        )
        if node == 0:
            return net_outflow == network.throughput
        if node == 6:
            return net_outflow == -network.throughput
        return net_outflow == 0

    model.flow_balance = pyo.Constraint(
        model.nodes,
        rule=balance_rule,
    )
    model.total_flow = pyo.Objective(
        expr=model.throughput,
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPsi raises this when it cannot load a feasible solution.
        # Preserve unexpected runtime errors.
        if "A feasible solution was not found" not in str(exc):
            raise

    try:
        obj_val = float(pyo.value(model.total_flow))
    except (ValueError, TypeError):
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}