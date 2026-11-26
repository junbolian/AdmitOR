# IR: {"sets":{"N":"{0,...,8}","R":"{1,...,7}","A":"N x N"},"params":{"capacity_matrix":"9x9 nonnegative capacities read from params['capacity_matrix']"},"variables":{"flow[i,j]":"NonNegativeReals for (i,j) in A"},"constraints":["flow[i,j] <= capacity_matrix[i][j] for (i,j) in A","sum(flow[j,i] for j in N) = sum(flow[i,j] for j in N) for i in R"],"objective":"maximize sum(flow[0,j] for j in N) - sum(flow[j,0] for j in N)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    capacity_matrix = params["capacity_matrix"]

    model = pyo.ConcreteModel()
    model.nodes = pyo.RangeSet(0, 8)
    model.relay_nodes = pyo.RangeSet(1, 7)

    model.capacity = pyo.Param(
        model.nodes,
        model.nodes,
        initialize=lambda _, i, j: capacity_matrix[i][j],
        within=pyo.NonNegativeReals,
    )

    model.flow = pyo.Var(
        model.nodes,
        model.nodes,
        domain=pyo.NonNegativeReals,
    )

    def capacity_rule(_, i, j):
        return model.flow[i, j] <= model.capacity[i, j]

    model.capacity_limits = pyo.Constraint(
        model.nodes,
        model.nodes,
        rule=capacity_rule,
    )

    def conservation_rule(_, i):
        return (
            sum(model.flow[j, i] for j in model.nodes)
            == sum(model.flow[i, j] for j in model.nodes)
        )

    model.flow_conservation = pyo.Constraint(
        model.relay_nodes,
        rule=conservation_rule,
    )

    model.throughput = pyo.Objective(
        expr=(
            sum(model.flow[0, j] for j in model.nodes)
            - sum(model.flow[j, 0] for j in model.nodes)
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.throughput))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}