# IR: {"sets":{"N":[0,1,2,3,4,5,6],"A":"{(i,j) in N x N: i != j}","I":[1,2,3,4,5]},"params":{"capacity[i,j]":"params[f'capacity_{i}_{j}'] for (i,j) in A"},"variables":{"flow[i,j]":{"type":"continuous","lower_bound":0,"index":"A"}},"constraints":["flow[i,j] <= capacity[i,j] for (i,j) in A","sum(flow[k,j] for j != k) == sum(flow[i,k] for i != k) for k in I"],"objective":{"sense":"maximize","expression":"sum(flow[0,j] for j != 0) - sum(flow[i,0] for i != 0)"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.nodes = pyo.Set(initialize=range(7), ordered=True)
    model.arcs = pyo.Set(
        dimen=2,
        initialize=[
            (i, j)
            for i in range(7)
            for j in range(7)
            if i != j
        ],
        ordered=True,
    )
    model.intermediate_nodes = pyo.Set(initialize=range(1, 6), ordered=True)

    model.link_capacity = pyo.Param(
        model.arcs,
        initialize={
            (i, j): params[f"capacity_{i}_{j}"]
            for i, j in model.arcs
        },
        within=pyo.Reals,
    )

    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    def capacity_rule(model, i, j):
        return model.flow[i, j] <= model.link_capacity[i, j]

    model.capacity_limits = pyo.Constraint(
        model.arcs,
        rule=capacity_rule,
    )

    def conservation_rule(model, k):
        return (
            sum(model.flow[k, j] for j in model.nodes if j != k)
            == sum(model.flow[i, k] for i in model.nodes if i != k)
        )

    model.flow_conservation = pyo.Constraint(
        model.intermediate_nodes,
        rule=conservation_rule,
    )

    model.max_flow_objective = pyo.Objective(
        expr=(
            sum(model.flow[0, j] for j in model.nodes if j != 0)
            - sum(model.flow[i, 0] for i in model.nodes if i != 0)
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.max_flow_objective))
    except (ValueError, TypeError):
        return {"objective": None, "status": "no_objective"}

    return {"objective": obj_val, "status": "optimal"}