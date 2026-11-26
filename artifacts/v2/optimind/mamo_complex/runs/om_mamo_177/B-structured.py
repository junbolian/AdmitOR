# IR: {"sets":{"V":"{0,...,7}","A":"{(i,j) in V x V: i != j}","T":"{1,...,6}"},"params":{"arc_capacities":"Nonnegative capacities c[i,j], supplied as an 8x8 nested array, a flat 64-element row-major array, or a mapping with tuple keys, nested keys, or flat row-major integer keys"},"variables":{"flow[i,j]":"continuous nonnegative for (i,j) in A"},"constraints":["flow[i,j] <= c[i,j] for every (i,j) in A","sum(flow[i,j] for i in V if i != j) = sum(flow[j,k] for k in V if k != j) for every j in T"],"objective":"maximize sum(flow[0,j] for j in V if j != 0) - sum(flow[i,0] for i in V if i != 0)"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    capacities = params["arc_capacities"]
    node_count = 8

    def read_capacity(tail, head):
        if isinstance(capacities, Mapping) and (tail, head) in capacities:
            return capacities[(tail, head)]

        if len(capacities) == node_count * node_count:
            return capacities[node_count * tail + head]

        return capacities[tail][head]

    model = pyo.ConcreteModel()
    model.nodes = pyo.RangeSet(0, node_count - 1)
    model.transit_nodes = pyo.RangeSet(1, node_count - 2)
    model.arcs = pyo.Set(
        dimen=2,
        initialize=[
            (tail, head)
            for tail in range(node_count)
            for head in range(node_count)
            if tail != head
        ],
    )

    model.capacity = pyo.Param(
        model.arcs,
        initialize=lambda instance, tail, head: read_capacity(tail, head),
        within=pyo.NonNegativeReals,
    )
    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    def capacity_limit_rule(instance, tail, head):
        return instance.flow[tail, head] <= instance.capacity[tail, head]

    model.capacity_limits = pyo.Constraint(
        model.arcs,
        rule=capacity_limit_rule,
    )

    def conservation_rule(instance, node):
        return sum(
            instance.flow[tail, node]
            for tail in instance.nodes
            if tail != node
        ) == sum(
            instance.flow[node, head]
            for head in instance.nodes
            if head != node
        )

    model.flow_conservation = pyo.Constraint(
        model.transit_nodes,
        rule=conservation_rule,
    )

    model.total_flow = pyo.Objective(
        expr=(
            sum(model.flow[0, head] for head in model.nodes if head != 0)
            - sum(model.flow[tail, 0] for tail in model.nodes if tail != 0)
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "A feasible solution was not found" not in str(exc):
            raise

    try:
        obj_val = float(pyo.value(model.total_flow))
    except ValueError:
        return {"objective": None, "status": "no_solution"}

    return {"objective": obj_val, "status": "optimal"}