# IR: {"sets":{"N":"0..15","T":"1..15","D":"0..1","A":"{(i,j): i in N, j in T, i != j}"},"params":{"K":"params['max_turbines_per_feeder'], nonnegative finite","c":"params['cable_cost_matrix'], symmetric 16x16","coordinates":"params['node_coordinates'], 16x2; descriptive data"},"variables":{"x[i,j]":"binary for (i,j) in A; selected parent-to-child cable","f[i,j]":"nonnegative continuous for (i,j) in A; downstream turbine count"},"constraints":["For each j in T: sum(x[i,j] for i in N if i != j) = 1.","For each j in T: sum(f[i,j] for i in N if i != j) - sum(f[j,k] for k in T if k != j) = 1.","sum(f[0,j] for j in T) = 15.","For each (i,j) in A: x[i,j] <= f[i,j] <= K*x[i,j]."],"objective":"Minimize sum(c[i,j]*x[i,j] for (i,j) in A)."}
import math

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    capacity = float(params["max_turbines_per_feeder"])
    costs = params["cable_cost_matrix"]
    coordinates = params["node_coordinates"]

    nodes = range(16)
    turbines = range(1, 16)
    dimensions = range(2)

    if not math.isfinite(capacity) or capacity < 0:
        raise ValueError("max_turbines_per_feeder must be finite and nonnegative.")
    if len(costs) != len(nodes) or any(
        len(row) != len(nodes) for row in costs
    ):
        raise ValueError("cable_cost_matrix must have shape 16x16.")
    if len(coordinates) != len(nodes) or any(
        len(point) != len(dimensions) for point in coordinates
    ):
        raise ValueError("node_coordinates must have shape 16x2.")

    cost_data = {
        (i, j): float(costs[i][j])
        for i in nodes
        for j in nodes
    }
    coordinate_data = {
        (i, d): float(coordinates[i][d])
        for i in nodes
        for d in dimensions
    }

    if not all(math.isfinite(value) for value in cost_data.values()):
        raise ValueError("Cable costs must be finite.")
    if not all(math.isfinite(value) for value in coordinate_data.values()):
        raise ValueError("Node coordinates must be finite.")
    if any(
        cost_data[i, j] != cost_data[j, i]
        for i in nodes
        for j in nodes
        if i < j
    ):
        raise ValueError("cable_cost_matrix must be symmetric.")

    model = pyo.ConcreteModel()
    model.N = pyo.Set(initialize=nodes, ordered=True)
    model.T = pyo.Set(initialize=turbines, ordered=True)
    model.D = pyo.Set(initialize=dimensions, ordered=True)
    model.A = pyo.Set(
        dimen=2,
        initialize=[
            (i, j)
            for i in nodes
            for j in turbines
            if i != j
        ],
    )

    model.K = pyo.Param(initialize=capacity, within=pyo.NonNegativeReals)
    model.c = pyo.Param(
        model.N, model.N, initialize=cost_data, within=pyo.Reals
    )
    model.coordinates = pyo.Param(
        model.N, model.D, initialize=coordinate_data, within=pyo.Reals
    )

    model.x = pyo.Var(model.A, domain=pyo.Binary)
    model.f = pyo.Var(model.A, domain=pyo.NonNegativeReals)

    def parent_rule(mdl, j):
        return sum(
            mdl.x[i, j] for i in mdl.N if i != j
        ) == 1

    model.one_parent = pyo.Constraint(model.T, rule=parent_rule)

    def flow_balance_rule(mdl, j):
        incoming = sum(mdl.f[i, j] for i in mdl.N if i != j)
        outgoing = sum(mdl.f[j, k] for k in mdl.T if k != j)
        return incoming - outgoing == 1

    model.flow_balance = pyo.Constraint(
        model.T, rule=flow_balance_rule
    )
    model.root_supply = pyo.Constraint(
        expr=sum(model.f[0, j] for j in model.T) == len(turbines)
    )

    def flow_lower_rule(mdl, i, j):
        return mdl.f[i, j] >= mdl.x[i, j]

    def flow_upper_rule(mdl, i, j):
        return mdl.f[i, j] <= mdl.K * mdl.x[i, j]

    model.flow_lower = pyo.Constraint(model.A, rule=flow_lower_rule)
    model.flow_upper = pyo.Constraint(model.A, rule=flow_upper_rule)

    # Flow conservation excludes disconnected cycles. Each root cable's flow
    # equals the number of turbines in its feeder subtree.
    model.total_cost = pyo.Objective(
        expr=sum(
            model.c[i, j] * model.x[i, j]
            for i, j in model.A
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "a feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}