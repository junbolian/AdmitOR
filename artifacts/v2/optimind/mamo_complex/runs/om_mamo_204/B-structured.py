# IR: {"sets":{"N":"{0,...,7}","A":"{(i,j) in N x N: i != j}","T":"{1,...,6}"},"params":{"capacity":"nonnegative 8x8 matrix from params['capacity']"},"variables":{"flow[i,j]":"nonnegative continuous for (i,j) in A"},"constraints":["flow[i,j] <= capacity[i,j] for (i,j) in A","sum(flow[i,j] for j != i) = sum(flow[j,i] for j != i) for i in T"],"objective":"maximize sum(flow[0,j] for j != 0) - sum(flow[j,0] for j != 0)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    capacity = params["capacity"]

    model = pyo.ConcreteModel()
    model.nodes = pyo.RangeSet(0, 7)
    model.transit_nodes = pyo.RangeSet(1, 6)
    model.arcs = pyo.Set(
        dimen=2,
        initialize=[
            (i, j)
            for i in range(8)
            for j in range(8)
            if i != j
        ],
    )

    model.line_capacity = pyo.Param(
        model.nodes,
        model.nodes,
        initialize=lambda mdl, i, j: capacity[i][j],
        within=pyo.NonNegativeReals,
    )
    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    def capacity_rule(mdl, i, j):
        return mdl.flow[i, j] <= mdl.line_capacity[i, j]

    model.capacity_limits = pyo.Constraint(
        model.arcs, rule=capacity_rule
    )

    def conservation_rule(mdl, i):
        outgoing = sum(
            mdl.flow[i, j] for j in mdl.nodes if j != i
        )
        incoming = sum(
            mdl.flow[j, i] for j in mdl.nodes if j != i
        )
        return outgoing == incoming

    model.flow_conservation = pyo.Constraint(
        model.transit_nodes, rule=conservation_rule
    )

    model.total_flow = pyo.Objective(
        expr=(
            sum(model.flow[0, j] for j in model.nodes if j != 0)
            - sum(model.flow[j, 0] for j in model.nodes if j != 0)
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_flow))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}