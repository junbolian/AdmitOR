# IR: {"sets":{"N":"range(params['num_nodes'])","S":"N excluding depot 0","A":"{(i,j) in N x N: i != j}","D":"{0,1}"},"params":{"num_nodes":"params['num_nodes']; frozen node count","distance":"params['distance_matrix'][i][j] for i,j in N","coordinates":"params['node_coordinates'][i][d] for i in N,d in D; metadata only"},"variables":{"x[i,j]":"binary for (i,j) in A; selected directed travel arc","u[i]":"continuous in [1,num_nodes-1] for i in S; visit order"},"constraints":["sum(x[i,j] for j in N if j != i) = 1 for every i in N","sum(x[i,j] for i in N if i != j) = 1 for every j in N","u[i]-u[j]+(num_nodes-1)*x[i,j] <= num_nodes-2 for distinct i,j in S"],"objective":"minimize sum(distance[i,j]*x[i,j] for (i,j) in A); selected arcs define one tour starting and ending at node 0"}
import operator

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_nodes = operator.index(params["num_nodes"])
    distance_matrix = params["distance_matrix"]
    node_coordinates = params["node_coordinates"]

    model = pyo.ConcreteModel()

    model.node_count = pyo.Param(
        initialize=num_nodes,
        within=pyo.PositiveIntegers,
    )
    model.N = pyo.Set(initialize=range(num_nodes), ordered=True)
    model.S = pyo.Set(
        initialize=range(1, num_nodes),
        within=model.N,
        ordered=True,
    )
    model.A = pyo.Set(
        dimen=2,
        initialize=(
            (i, j)
            for i in range(num_nodes)
            for j in range(num_nodes)
            if i != j
        ),
    )
    model.D = pyo.Set(initialize=(0, 1), ordered=True)

    model.distance = pyo.Param(
        model.N,
        model.N,
        initialize=lambda mdl, i, j: distance_matrix[i][j],
        within=pyo.Reals,
    )
    model.coordinates = pyo.Param(
        model.N,
        model.D,
        initialize=lambda mdl, i, d: node_coordinates[i][d],
        within=pyo.Reals,
    )

    model.x = pyo.Var(model.A, domain=pyo.Binary)
    model.u = pyo.Var(
        model.S,
        domain=pyo.Reals,
        bounds=(1, num_nodes - 1),
    )

    def outgoing_rule(mdl, i):
        return sum(mdl.x[i, j] for j in mdl.N if j != i) == 1

    model.outgoing = pyo.Constraint(model.N, rule=outgoing_rule)

    def incoming_rule(mdl, j):
        return sum(mdl.x[i, j] for i in mdl.N if i != j) == 1

    model.incoming = pyo.Constraint(model.N, rule=incoming_rule)

    def subtour_rule(mdl, i, j):
        if i == j:
            return pyo.Constraint.Skip
        return (
            mdl.u[i] - mdl.u[j] + (mdl.node_count - 1) * mdl.x[i, j]
            <= mdl.node_count - 2
        )

    model.subtour = pyo.Constraint(model.S, model.S, rule=subtour_rule)

    model.total_cost = pyo.Objective(
        expr=sum(
            model.distance[i, j] * model.x[i, j]
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