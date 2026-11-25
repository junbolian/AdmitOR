# IR: {"sets":{"N":"range(num_nodes)","B":"N excluding depot 0","A":"{(i,j) in N x N: i != j}","K":[0,1]},"params":{"num_nodes":"params['num_nodes']","distance":"params['distance_matrix'][i][j] for i,j in N","coordinate":"params['coordinates'][i][k] for i in N,k in K; descriptive metadata"},"variables":{"x[i,j]":"Binary for (i,j) in A","u[i]":"Real in [1,num_nodes-1] for i in B"},"constraints":["outgoing[i]: sum(x[i,j] for j in N if j != i) = 1 for i in N","incoming[j]: sum(x[i,j] for i in N if i != j) = 1 for j in N","subtour[i,j]: u[i]-u[j]+num_nodes*x[i,j] <= num_nodes-1 for distinct i,j in B"],"objective":"minimize sum(distance[i,j]*x[i,j] for (i,j) in A)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_nodes = params["num_nodes"]
    distance_matrix = params["distance_matrix"]
    coordinates = params["coordinates"]

    model = pyo.ConcreteModel()

    model.node_set = pyo.Set(
        initialize=range(num_nodes), ordered=True
    )
    model.bin_set = pyo.Set(
        initialize=range(1, num_nodes), ordered=True
    )
    model.arc_set = pyo.Set(
        dimen=2,
        initialize=(
            (i, j)
            for i in range(num_nodes)
            for j in range(num_nodes)
            if i != j
        ),
    )
    model.axis_set = pyo.Set(initialize=(0, 1), ordered=True)

    model.node_count = pyo.Param(
        initialize=num_nodes, within=pyo.PositiveIntegers
    )
    model.route_distance = pyo.Param(
        model.node_set,
        model.node_set,
        initialize=lambda mdl, i, j: distance_matrix[i][j],
        within=pyo.NonNegativeReals,
    )
    model.node_coordinate = pyo.Param(
        model.node_set,
        model.axis_set,
        initialize=lambda mdl, i, k: coordinates[i][k],
        within=pyo.Reals,
    )

    model.x = pyo.Var(model.arc_set, domain=pyo.Binary)
    model.u = pyo.Var(
        model.bin_set,
        domain=pyo.Reals,
        bounds=(1, num_nodes - 1),
    )

    def outgoing_rule(mdl, i):
        return sum(
            mdl.x[i, j] for j in mdl.node_set if j != i
        ) == 1

    model.outgoing = pyo.Constraint(
        model.node_set, rule=outgoing_rule
    )

    def incoming_rule(mdl, j):
        return sum(
            mdl.x[i, j] for i in mdl.node_set if i != j
        ) == 1

    model.incoming = pyo.Constraint(
        model.node_set, rule=incoming_rule
    )

    def subtour_rule(mdl, i, j):
        if i == j:
            return pyo.Constraint.Skip
        return (
            mdl.u[i] - mdl.u[j] + mdl.node_count * mdl.x[i, j]
            <= mdl.node_count - 1
        )

    model.subtour = pyo.Constraint(
        model.bin_set, model.bin_set, rule=subtour_rule
    )

    model.total_distance = pyo.Objective(
        expr=sum(
            model.route_distance[i, j] * model.x[i, j]
            for i, j in model.arc_set
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_distance))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}