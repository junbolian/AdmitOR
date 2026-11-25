# IR: {"sets":{"N":"{0,...,8}","R":"N\\{0}","A":"{(i,j) in N x N: i != j}","K":"{0,1}"},"params":{"distance_matrix":"nonnegative distances d[i,j], read from params","node_coordinates":"real coordinates c[i,k], read from params; descriptive metadata"},"variables":{"x[i,j]":"binary for (i,j) in A","u[i]":"continuous in [1,|R|] for i in R"},"constraints":["sum(x[i,j] for j in N if j != i) = 1 for each i in N","sum(x[i,j] for i in N if i != j) = 1 for each j in N","u[i] - u[j] + |R|*x[i,j] <= |R|-1 for distinct i,j in R"],"objective":"minimize sum(d[i,j]*x[i,j] for (i,j) in A)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    distance_matrix = params["distance_matrix"]
    node_coordinates = params["node_coordinates"]

    model = pyo.ConcreteModel()

    model.nodes = pyo.RangeSet(0, 8)
    model.outlets = pyo.RangeSet(1, 8)
    model.coordinate_axes = pyo.RangeSet(0, 1)
    model.arcs = pyo.Set(
        dimen=2,
        initialize=[
            (i, j)
            for i in model.nodes
            for j in model.nodes
            if i != j
        ],
    )

    model.distances = pyo.Param(
        model.nodes,
        model.nodes,
        initialize=lambda mdl, i, j: distance_matrix[i][j],
        within=pyo.NonNegativeReals,
    )
    model.coordinates = pyo.Param(
        model.nodes,
        model.coordinate_axes,
        initialize=lambda mdl, i, k: node_coordinates[i][k],
        within=pyo.Reals,
    )

    outlet_count = len(model.outlets)

    model.x = pyo.Var(model.arcs, domain=pyo.Binary)
    model.u = pyo.Var(
        model.outlets,
        domain=pyo.Reals,
        bounds=(1, outlet_count),
    )

    def departure_rule(mdl, i):
        return sum(
            mdl.x[i, j] for j in mdl.nodes if j != i
        ) == 1

    model.departures = pyo.Constraint(
        model.nodes,
        rule=departure_rule,
    )

    def arrival_rule(mdl, j):
        return sum(
            mdl.x[i, j] for i in mdl.nodes if i != j
        ) == 1

    model.arrivals = pyo.Constraint(
        model.nodes,
        rule=arrival_rule,
    )

    def subtour_rule(mdl, i, j):
        if i == j:
            return pyo.Constraint.Skip
        return (
            mdl.u[i] - mdl.u[j] + outlet_count * mdl.x[i, j]
            <= outlet_count - 1
        )

    model.subtour_elimination = pyo.Constraint(
        model.outlets,
        model.outlets,
        rule=subtour_rule,
    )

    model.total_distance = pyo.Objective(
        expr=sum(
            model.distances[i, j] * model.x[i, j]
            for i, j in model.arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "A feasible solution was not found" in str(exc):
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_distance))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}