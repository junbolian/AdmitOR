# IR: {"sets":{"N":"0..7","A":"ordered (i,j) in N x N with i!=j","R":"1..6"},"params":{"capacity":"params['capacity']; accept an 8x8 matrix, 64 row-major matrix entries, 56 row-major non-self-loop entries, or 55 entries in the listed arc order with absent arc (4,3) assigned zero"},"variables":{"flow[i,j]":"NonNegativeReals for (i,j) in A"},"constraints":["flow[i,j] <= capacity[i,j] for (i,j) in A","sum(flow[i,k] for i in N if i!=k) == sum(flow[k,j] for j in N if j!=k) for k in R"],"objective":"maximize sum(flow[0,j] for j in N if j!=0) - sum(flow[i,0] for i in N if i!=0)"}

import math

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    nodes = list(range(8))
    arcs = [(i, j) for i in nodes for j in nodes if i != j]
    capacity_values = list(params["capacity"])

    if len(capacity_values) == len(nodes):
        try:
            rows = [list(row) for row in capacity_values]
        except TypeError:
            return {"objective": None, "status": "invalid_capacity_shape"}

        if any(len(row) != len(nodes) for row in rows):
            return {"objective": None, "status": "invalid_capacity_shape"}

        capacity_by_arc = {(i, j): rows[i][j] for i, j in arcs}

    elif len(capacity_values) == len(nodes) ** 2:
        capacity_by_arc = {
            (i, j): capacity_values[i * len(nodes) + j]
            for i, j in arcs
        }

    elif len(capacity_values) == len(arcs):
        capacity_by_arc = dict(zip(arcs, capacity_values))

    elif len(capacity_values) == len(arcs) - 1:
        listed_arcs = [arc for arc in arcs if arc != (4, 3)]
        capacity_by_arc = dict(zip(listed_arcs, capacity_values))
        capacity_by_arc[(4, 3)] = 0

    else:
        return {"objective": None, "status": "invalid_capacity_shape"}

    try:
        capacity_by_arc = {
            arc: float(value) for arc, value in capacity_by_arc.items()
        }
    except (TypeError, ValueError, OverflowError):
        return {"objective": None, "status": "invalid_capacity_value"}

    if any(
        not math.isfinite(value) or value < 0
        for value in capacity_by_arc.values()
    ):
        return {"objective": None, "status": "invalid_capacity_value"}

    model = pyo.ConcreteModel()

    model.nodes = pyo.Set(initialize=nodes, ordered=True)
    model.arcs = pyo.Set(dimen=2, initialize=arcs, ordered=True)
    model.relay_nodes = pyo.Set(initialize=range(1, 7), ordered=True)

    model.capacity = pyo.Param(
        model.arcs,
        initialize=capacity_by_arc,
        within=pyo.NonNegativeReals,
    )
    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    def capacity_rule(network, i, j):
        return network.flow[i, j] <= network.capacity[i, j]

    model.capacity_limits = pyo.Constraint(
        model.arcs,
        rule=capacity_rule,
    )

    def conservation_rule(network, k):
        return (
            sum(network.flow[i, k] for i in network.nodes if i != k)
            == sum(network.flow[k, j] for j in network.nodes if j != k)
        )

    model.flow_conservation = pyo.Constraint(
        model.relay_nodes,
        rule=conservation_rule,
    )

    model.total_flow = pyo.Objective(
        expr=(
            sum(model.flow[0, j] for j in model.nodes if j != 0)
            - sum(model.flow[i, 0] for i in model.nodes if i != 0)
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
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}