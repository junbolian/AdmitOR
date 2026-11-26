# IR: {"sets":{"N":"0..8","A":"{(i,j) in N x N: i != j and (i,j) != (3,2)}"},"params":{"capacity[i,j]":"params[f'cap_{i}_{j}'] for (i,j) in A"},"variables":{"flow[i,j]":"continuous nonnegative for (i,j) in A","throughput":"continuous nonnegative"},"constraints":["flow[i,j] <= capacity[i,j] for (i,j) in A","sum(flow[i,j] for outgoing arcs) - sum(flow[j,i] for incoming arcs) = throughput if i=0, -throughput if i=8, otherwise 0, for i in N"],"objective":"maximize throughput"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    nodes = tuple(range(9))
    arcs = tuple(
        (tail, head)
        for tail in nodes
        for head in nodes
        if tail != head and (tail, head) != (3, 2)
    )
    capacities = {
        (tail, head): params[f"cap_{tail}_{head}"]
        for tail, head in arcs
    }
    outgoing = {
        node: tuple(head for tail, head in arcs if tail == node)
        for node in nodes
    }
    incoming = {
        node: tuple(tail for tail, head in arcs if head == node)
        for node in nodes
    }

    model = pyo.ConcreteModel()
    model.sectors = pyo.Set(initialize=nodes, ordered=True)
    model.tubes = pyo.Set(dimen=2, initialize=arcs, ordered=True)
    model.capacity = pyo.Param(
        model.tubes,
        initialize=capacities,
        within=pyo.Reals,
    )
    model.flow = pyo.Var(model.tubes, domain=pyo.NonNegativeReals)
    model.throughput = pyo.Var(domain=pyo.NonNegativeReals)

    def capacity_rule(network, tail, head):
        return network.flow[tail, head] <= network.capacity[tail, head]

    model.capacity_limits = pyo.Constraint(
        model.tubes,
        rule=capacity_rule,
    )

    def balance_rule(network, node):
        net_outflow = (
            sum(network.flow[node, head] for head in outgoing[node])
            - sum(network.flow[tail, node] for tail in incoming[node])
        )
        if node == 0:
            return net_outflow == network.throughput
        if node == 8:
            return net_outflow == -network.throughput
        return net_outflow == 0

    model.flow_balances = pyo.Constraint(
        model.sectors,
        rule=balance_rule,
    )
    model.max_flow_objective = pyo.Objective(
        expr=model.throughput,
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "A feasible solution was not found" in str(exc):
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.max_flow_objective))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}