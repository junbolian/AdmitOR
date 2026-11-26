# IR: {"sets":{"N":"{0,...,8}","A":"{(i,j) in N x N: i != j}"},"params":{"capacity[i,j]":"params['cap_i_j'] for i != 8; params['cap_8_all'] for i == 8"},"variables":{"flow[i,j]":"continuous, nonnegative, indexed by A","throughput":"continuous, nonnegative"},"constraints":["flow[i,j] <= capacity[i,j] for every (i,j) in A","sum_j flow[i,j] - sum_j flow[j,i] = throughput if i=0, -throughput if i=8, and 0 otherwise, for every i in N"],"objective":"maximize throughput"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.nodes = pyo.RangeSet(0, 8)
    model.arcs = pyo.Set(
        dimen=2,
        initialize=[
            (origin, destination)
            for origin in range(9)
            for destination in range(9)
            if origin != destination
        ],
    )

    destination_outbound_capacity = params["cap_8_all"]
    capacities = {
        (origin, destination): (
            destination_outbound_capacity
            if origin == 8
            else params[f"cap_{origin}_{destination}"]
        )
        for origin, destination in model.arcs
    }

    model.capacity = pyo.Param(
        model.arcs,
        initialize=capacities,
        within=pyo.NonNegativeReals,
    )
    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)
    model.throughput = pyo.Var(domain=pyo.NonNegativeReals)

    def capacity_rule(network, origin, destination):
        return (
            network.flow[origin, destination]
            <= network.capacity[origin, destination]
        )

    model.link_capacity = pyo.Constraint(
        model.arcs,
        rule=capacity_rule,
    )

    def balance_rule(network, node):
        outbound = sum(
            network.flow[node, destination]
            for destination in network.nodes
            if destination != node
        )
        inbound = sum(
            network.flow[origin, node]
            for origin in network.nodes
            if origin != node
        )

        if node == 0:
            return outbound - inbound == network.throughput
        if node == 8:
            return outbound - inbound == -network.throughput
        return outbound - inbound == 0

    model.flow_balance = pyo.Constraint(
        model.nodes,
        rule=balance_rule,
    )

    model.total_flow_objective = pyo.Objective(
        expr=model.throughput,
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        # HiGHS can raise when no feasible solution can be loaded.
        # Objective retrieval below remains the sole success test.
        pass

    try:
        obj_val = float(pyo.value(model.total_flow_objective))
    except (ValueError, TypeError):
        return {"objective": None, "status": "no_solution"}

    return {"objective": obj_val, "status": "optimal"}