# IR: {"sets":{"V":"{0,...,7}","A":"{(i,j) in V x V: i != j}"},"params":{"capacity[i,j]":"params[f'capacity_{i}_{j}'] for every (i,j) in A"},"variables":{"flow[i,j]":"continuous nonnegative for (i,j) in A","throughput":"continuous nonnegative"},"constraints":["flow[i,j] <= capacity[i,j] for every (i,j) in A","sum_j flow[v,j] - sum_i flow[i,v] = throughput if v=0, -throughput if v=7, and 0 otherwise, for every v in V"],"objective":"maximize throughput"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.vertices = pyo.RangeSet(0, 7)
    model.arcs = pyo.Set(
        dimen=2,
        initialize=[
            (i, j)
            for i in range(8)
            for j in range(8)
            if i != j
        ],
    )

    model.capacity = pyo.Param(
        model.arcs,
        initialize={
            (i, j): params[f"capacity_{i}_{j}"]
            for i, j in model.arcs
        },
        within=pyo.NonNegativeReals,
    )

    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)
    model.throughput = pyo.Var(domain=pyo.NonNegativeReals)

    def capacity_rule(network, i, j):
        return network.flow[i, j] <= network.capacity[i, j]

    model.capacity_limits = pyo.Constraint(
        model.arcs,
        rule=capacity_rule,
    )

    def balance_rule(network, vertex):
        outgoing = sum(
            network.flow[vertex, j]
            for j in network.vertices
            if j != vertex
        )
        incoming = sum(
            network.flow[i, vertex]
            for i in network.vertices
            if i != vertex
        )

        if vertex == 0:
            return outgoing - incoming == network.throughput
        if vertex == 7:
            return outgoing - incoming == -network.throughput
        return outgoing - incoming == 0

    model.flow_balance = pyo.Constraint(
        model.vertices,
        rule=balance_rule,
    )

    model.max_throughput = pyo.Objective(
        expr=model.throughput,
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPsi raises this specific error when no solution can be loaded.
        # Still determine success solely by retrieving the objective below.
        if "a feasible solution was not found" not in str(exc).lower():
            raise

    try:
        obj_val = float(pyo.value(model.max_throughput))
    except ValueError:
        return {"objective": None, "status": "no_solution"}

    return {"objective": obj_val, "status": "optimal"}