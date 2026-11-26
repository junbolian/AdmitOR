# IR: {
#   "sets": {"V": "range(params['num_nodes'])", "A": [[0,1],[0,2],[0,3],[0,4],[0,5],[1,0],[1,2],[1,3],[1,5],[2,0],[2,1],[2,3],[2,4],[3,0],[3,1],[3,2],[3,4],[4,0],[4,2],[4,3],[4,5],[5,0],[5,1],[5,2],[5,3],[5,4]]},
#   "params": {"capacity[i,j]": "params['capacity_' + str(i) + '_' + str(j)] for (i,j) in A", "num_nodes": "params['num_nodes']", "source": "params['source_node']", "sink": "params['sink_node']"},
#   "variables": {"flow[i,j]": "nonnegative continuous for (i,j) in A", "throughput": "nonnegative continuous"},
#   "constraints": ["flow[i,j] <= capacity[i,j] for (i,j) in A", "sum(flow[v,j] for outgoing arcs) - sum(flow[i,v] for incoming arcs) = throughput if v=source, -throughput if v=sink, otherwise 0, for v in V"],
#   "objective": "maximize throughput"
# }

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_nodes = params["num_nodes"]
    source = params["source_node"]
    sink = params["sink_node"]

    arcs = (
        (0, 1), (0, 2), (0, 3), (0, 4), (0, 5),
        (1, 0), (1, 2), (1, 3), (1, 5),
        (2, 0), (2, 1), (2, 3), (2, 4),
        (3, 0), (3, 1), (3, 2), (3, 4),
        (4, 0), (4, 2), (4, 3), (4, 5),
        (5, 0), (5, 1), (5, 2), (5, 3), (5, 4),
    )

    capacities = {
        (tail, head): params[f"capacity_{tail}_{head}"]
        for tail, head in arcs
    }

    # Six nodes are part of the fixed network structure.
    if (
        num_nodes != 6
        or source not in range(num_nodes)
        or sink not in range(num_nodes)
        or source == sink
    ):
        return {"objective": None, "status": "invalid_network"}

    model = pyo.ConcreteModel()
    model.node_set = pyo.Set(initialize=range(num_nodes), ordered=True)
    model.arc_set = pyo.Set(dimen=2, initialize=arcs, ordered=True)

    model.edge_capacity = pyo.Param(
        model.arc_set,
        initialize=capacities,
        within=pyo.NonNegativeReals,
    )

    model.flow = pyo.Var(model.arc_set, domain=pyo.NonNegativeReals)
    model.throughput = pyo.Var(domain=pyo.NonNegativeReals)

    outgoing = {
        node: tuple(head for tail, head in arcs if tail == node)
        for node in range(num_nodes)
    }
    incoming = {
        node: tuple(tail for tail, head in arcs if head == node)
        for node in range(num_nodes)
    }

    def capacity_rule(network, tail, head):
        return network.flow[tail, head] <= network.edge_capacity[tail, head]

    model.capacity_limits = pyo.Constraint(
        model.arc_set,
        rule=capacity_rule,
    )

    def balance_rule(network, node):
        net_outflow = (
            pyo.quicksum(network.flow[node, head] for head in outgoing[node])
            - pyo.quicksum(network.flow[tail, node] for tail in incoming[node])
        )
        if node == source:
            return net_outflow == network.throughput
        if node == sink:
            return net_outflow == -network.throughput
        return net_outflow == 0

    model.flow_balance = pyo.Constraint(
        model.node_set,
        rule=balance_rule,
    )

    model.max_flow_objective = pyo.Objective(
        expr=model.throughput,
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPsi raises this error when its default solution loading fails
        # because no feasible solution is available.
        if "a feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.max_flow_objective))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}