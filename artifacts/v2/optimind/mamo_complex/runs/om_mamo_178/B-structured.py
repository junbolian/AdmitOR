# IR: {"sets":{"N":"{0,...,8}","A":"{(i,j) in N x N: i != j}","T":"{1,...,7}"},"params":{"capacity_matrix":"params['capacity_matrix']; flat row-major 9x9 array","capacity[i,j]":"capacity_matrix[9*i+j] for (i,j) in A; nonnegative"},"variables":{"flow[i,j]":{"type":"continuous","domain":"nonnegative","indices":"A"}},"constraints":["flow[i,j] <= capacity[i,j] for every (i,j) in A","sum(flow[i,j] for j != i) == sum(flow[j,i] for j != i) for every i in T"],"objective":{"sense":"maximize","expression":"sum(flow[0,j] for j != 0) - sum(flow[j,0] for j != 0)"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    capacity_matrix = params["capacity_matrix"]
    if len(capacity_matrix) != 9 * 9:
        raise ValueError("capacity_matrix must contain exactly 81 entries.")

    model = pyo.ConcreteModel()

    model.sectors = pyo.RangeSet(0, 8)
    model.intermediate_sectors = pyo.RangeSet(1, 7)
    model.arcs = pyo.Set(
        dimen=2,
        initialize=[
            (source, destination)
            for source in range(9)
            for destination in range(9)
            if source != destination
        ],
    )

    model.capacity = pyo.Param(
        model.arcs,
        initialize={
            (source, destination): capacity_matrix[9 * source + destination]
            for source, destination in model.arcs
        },
        within=pyo.NonNegativeReals,
    )
    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    def capacity_rule(network, source, destination):
        return (
            network.flow[source, destination]
            <= network.capacity[source, destination]
        )

    model.capacity_limits = pyo.Constraint(
        model.arcs, rule=capacity_rule
    )

    def conservation_rule(network, sector):
        outgoing = sum(
            network.flow[sector, destination]
            for destination in network.sectors
            if destination != sector
        )
        incoming = sum(
            network.flow[source, sector]
            for source in network.sectors
            if source != sector
        )
        return outgoing == incoming

    model.flow_conservation = pyo.Constraint(
        model.intermediate_sectors, rule=conservation_rule
    )

    model.total_flow = pyo.Objective(
        expr=(
            sum(model.flow[0, destination] for destination in range(1, 9))
            - sum(model.flow[source, 0] for source in range(1, 9))
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_flow))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}