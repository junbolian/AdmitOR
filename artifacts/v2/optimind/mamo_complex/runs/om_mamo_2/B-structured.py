# IR: {"sets":{"N":"0..8","A":"{(i,j) in N x N: i != j and C[i][j] > 0}"},"params":{"capacity_matrix":"params['capacity_matrix']; flat row-major length 81 or nested 9x9","C":"capacity_matrix normalized to 9x9"},"variables":{"flow[i,j]":"continuous nonnegative for (i,j) in A","total_flow":"continuous nonnegative"},"constraints":["flow[i,j] <= C[i][j] for (i,j) in A","outflow(i)-inflow(i) = total_flow for i=0, -total_flow for i=8, and 0 otherwise; isolated intermediate nodes satisfy this identically"],"objective":"maximize total_flow"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    raw_capacity = list(params["capacity_matrix"])

    if len(raw_capacity) == 81:
        capacity_matrix = [
            raw_capacity[9 * i:9 * (i + 1)]
            for i in range(9)
        ]
    elif len(raw_capacity) == 9:
        capacity_matrix = [list(row) for row in raw_capacity]
        if any(len(row) != 9 for row in capacity_matrix):
            return {"objective": None, "status": "invalid_shape"}
    else:
        return {"objective": None, "status": "invalid_shape"}

    model = pyo.ConcreteModel()
    model.nodes = pyo.RangeSet(0, 8)
    model.arcs = pyo.Set(
        dimen=2,
        initialize=[
            (i, j)
            for i in range(9)
            for j in range(9)
            if i != j and capacity_matrix[i][j] > 0
        ],
    )

    model.channel_capacity = pyo.Param(
        model.arcs,
        initialize={
            (i, j): capacity_matrix[i][j]
            for i, j in model.arcs
        },
        within=pyo.NonNegativeReals,
    )

    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)
    model.total_flow = pyo.Var(domain=pyo.NonNegativeReals)

    outgoing = {i: [] for i in model.nodes}
    incoming = {i: [] for i in model.nodes}
    for origin, destination in model.arcs:
        outgoing[origin].append((origin, destination))
        incoming[destination].append((origin, destination))

    def capacity_rule(instance, i, j):
        return instance.flow[i, j] <= instance.channel_capacity[i, j]

    model.capacity_limits = pyo.Constraint(
        model.arcs, rule=capacity_rule
    )

    def balance_rule(instance, i):
        net_outflow = (
            pyo.quicksum(instance.flow[arc] for arc in outgoing[i])
            - pyo.quicksum(instance.flow[arc] for arc in incoming[i])
        )

        if i == 0:
            return net_outflow == instance.total_flow
        if i == 8:
            return net_outflow == -instance.total_flow
        if not outgoing[i] and not incoming[i]:
            return pyo.Constraint.Feasible
        return net_outflow == 0

    model.flow_balance = pyo.Constraint(
        model.nodes, rule=balance_rule
    )
    model.max_flow_objective = pyo.Objective(
        expr=model.total_flow,
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.max_flow_objective))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}