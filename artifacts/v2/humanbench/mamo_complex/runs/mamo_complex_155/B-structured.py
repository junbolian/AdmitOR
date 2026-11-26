# IR: {"sets":{"N":"0..8","A":"{(i,j) in N x N: i != j}","T":"1..7"},"params":{"capacity_matrix":"input directed capacities","c[i,j]":"capacity_matrix[i][j] for (i,j) in A"},"variables":{"flow[i,j]":"continuous, nonnegative for (i,j) in A"},"constraints":["flow[i,j] <= c[i,j] for every (i,j) in A","sum(flow[i,j] for j != i) == sum(flow[j,i] for j != i) for every i in T"],"objective":"maximize sum(flow[0,j] for j != 0) - sum(flow[j,0] for j != 0)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    capacity_matrix = params["capacity_matrix"]

    model = pyo.ConcreteModel()
    model.stations = pyo.RangeSet(0, 8)
    model.transit_stations = pyo.RangeSet(1, 7)
    model.arcs = pyo.Set(
        dimen=2,
        initialize=[
            (i, j)
            for i in model.stations
            for j in model.stations
            if i != j
        ],
    )

    model.edge_capacity = pyo.Param(
        model.arcs,
        initialize=lambda instance, i, j: capacity_matrix[i][j],
        within=pyo.NonNegativeReals,
    )

    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    def capacity_rule(instance, i, j):
        return instance.flow[i, j] <= instance.edge_capacity[i, j]

    model.capacity_limits = pyo.Constraint(model.arcs, rule=capacity_rule)

    def conservation_rule(instance, i):
        return (
            sum(
                instance.flow[i, j]
                for j in instance.stations
                if j != i
            )
            == sum(
                instance.flow[j, i]
                for j in instance.stations
                if j != i
            )
        )

    model.flow_conservation = pyo.Constraint(
        model.transit_stations,
        rule=conservation_rule,
    )

    model.max_flow_objective = pyo.Objective(
        expr=(
            sum(model.flow[0, j] for j in model.stations if j != 0)
            - sum(model.flow[j, 0] for j in model.stations if j != 0)
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
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}