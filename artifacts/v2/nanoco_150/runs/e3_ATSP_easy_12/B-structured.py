# IR: {"sets":{"N":"{0,...,7}","D":"N excluding hub 0","A":"{(i,j) in N x N: i != j}","K":"{0,1}"},"params":{"cost_matrix":"params['cost_matrix']; real travel times indexed by N x N","coords":"params['coords']; real coordinates indexed by N x K; descriptive only"},"variables":{"x[i,j]":"binary for (i,j) in A","u[i]":"continuous in [1,|D|] for i in D"},"constraints":["For each i in N: sum(x[i,j] for j != i) = 1","For each j in N: sum(x[i,j] for i != j) = 1","For distinct i,j in D: u[i] - u[j] + |D|*x[i,j] <= |D|-1"],"objective":"Minimize sum(cost_matrix[i,j]*x[i,j] for (i,j) in A)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost_matrix = params["cost_matrix"]
    coords = params["coords"]

    num_nodes = 8
    num_deliveries = num_nodes - 1

    model = pyo.ConcreteModel()

    model.nodes = pyo.RangeSet(0, num_nodes - 1)
    model.deliveries = pyo.RangeSet(1, num_nodes - 1)
    model.coordinate_axes = pyo.RangeSet(0, 1)
    model.arcs = pyo.Set(
        dimen=2,
        initialize=(
            (i, j)
            for i in range(num_nodes)
            for j in range(num_nodes)
            if i != j
        ),
    )

    model.travel_time = pyo.Param(
        model.nodes,
        model.nodes,
        initialize=lambda mdl, i, j: cost_matrix[i][j],
        within=pyo.Reals,
    )
    model.location_coordinates = pyo.Param(
        model.nodes,
        model.coordinate_axes,
        initialize=lambda mdl, i, axis: coords[i][axis],
        within=pyo.Reals,
    )

    model.x = pyo.Var(model.arcs, domain=pyo.Binary)
    model.u = pyo.Var(
        model.deliveries,
        domain=pyo.Reals,
        bounds=(1, num_deliveries),
    )

    def outgoing_rule(mdl, i):
        return sum(mdl.x[i, j] for j in mdl.nodes if j != i) == 1

    model.outgoing_once = pyo.Constraint(
        model.nodes,
        rule=outgoing_rule,
    )

    def incoming_rule(mdl, j):
        return sum(mdl.x[i, j] for i in mdl.nodes if i != j) == 1

    model.incoming_once = pyo.Constraint(
        model.nodes,
        rule=incoming_rule,
    )

    def subtour_rule(mdl, i, j):
        if i == j:
            return pyo.Constraint.Skip
        return (
            mdl.u[i] - mdl.u[j] + num_deliveries * mdl.x[i, j]
            <= num_deliveries - 1
        )

    model.subtour_elimination = pyo.Constraint(
        model.deliveries,
        model.deliveries,
        rule=subtour_rule,
    )

    model.total_time = pyo.Objective(
        expr=sum(
            model.travel_time[i, j] * model.x[i, j]
            for i, j in model.arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_time))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}