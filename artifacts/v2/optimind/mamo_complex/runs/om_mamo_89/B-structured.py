# IR: {"sets":{"N":[0,1,2,3,4,5,6],"A":"{(i,j) in N x N: i != j}","T":[1,2,3,4,5]},"params":{"capacity[i,j]":"params[f'c{i}{j}'] for (i,j) in A"},"variables":{"flow[i,j]":"continuous, nonnegative for (i,j) in A"},"constraints":["flow[i,j] <= capacity[i,j] for (i,j) in A","sum(flow[i,j] for i in N if i != j) == sum(flow[j,k] for k in N if k != j) for j in T"],"objective":"maximize sum(flow[0,j] - flow[j,0] for j in N if j != 0)"}

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
    model.transit_nodes = pyo.Set(initialize=range(1, 6), ordered=True)

    model.capacity = pyo.Param(
        model.arcs,
        initialize={
            (i, j): params[f"c{i}{j}"]
            for i, j in model.arcs
        },
        within=pyo.Reals,
    )

    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    def capacity_rule(instance, i, j):
        return instance.flow[i, j] <= instance.capacity[i, j]

    model.capacity_limits = pyo.Constraint(
        model.arcs, rule=capacity_rule
    )

    def conservation_rule(instance, j):
        return (
            sum(
                instance.flow[i, j]
                for i in instance.nodes
                if i != j
            )
            == sum(
                instance.flow[j, k]
                for k in instance.nodes
                if k != j
            )
        )

    model.flow_conservation = pyo.Constraint(
        model.transit_nodes, rule=conservation_rule
    )

    model.total_flow = pyo.Objective(
        expr=sum(
            model.flow[0, j] - model.flow[j, 0]
            for j in model.nodes
            if j != 0
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPSI raises this when it cannot load a feasible solution.
        # Unexpected runtime errors propagate to the caller.
        if "a feasible solution was not found" not in str(exc).lower():
            raise

    try:
        obj_val = float(pyo.value(model.total_flow))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}