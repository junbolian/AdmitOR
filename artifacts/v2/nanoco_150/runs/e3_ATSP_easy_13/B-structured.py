# IR: {"sets":{"N":"{0,...,n_nodes-1}, with n_nodes=8","T":"N excluding 0","A":"{(i,j) in N x N: i != j}","D":"{0,1}"},"params":{"n_nodes":"params['n_nodes']","coords":"params['coords']; geographic metadata, not used to calculate costs","cost_matrix":"params['cost_matrix']; directed travel costs"},"variables":{"x[i,j]":"binary for (i,j) in A","u[i]":"continuous in [1,n_nodes-1] for i in T"},"constraints":["For every i in N: sum(x[i,j] for j in N if j != i) = 1","For every j in N: sum(x[i,j] for i in N if i != j) = 1","For every distinct i,j in T: u[i]-u[j]+(n_nodes-1)*x[i,j] <= n_nodes-2"],"objective":"Minimize sum(cost_matrix[i][j]*x[i,j] for (i,j) in A)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    n_nodes = params["n_nodes"]
    coords = params["coords"]
    cost_matrix = params["cost_matrix"]

    if isinstance(n_nodes, bool) or not isinstance(n_nodes, int) or n_nodes != 8:
        return {"objective": None, "status": "invalid_n_nodes"}

    model = pyo.ConcreteModel()

    model.N = pyo.Set(initialize=range(n_nodes), ordered=True)
    model.T = pyo.Set(initialize=range(1, n_nodes), ordered=True)
    model.A = pyo.Set(
        dimen=2,
        initialize=(
            (i, j)
            for i in range(n_nodes)
            for j in range(n_nodes)
            if i != j
        ),
        ordered=True,
    )
    model.D = pyo.Set(initialize=(0, 1), ordered=True)

    model.node_count = pyo.Param(
        initialize=n_nodes,
        within=pyo.PositiveIntegers,
    )
    model.site_coordinates = pyo.Param(
        model.N,
        model.D,
        initialize=lambda mdl, i, d: coords[i][d],
        within=pyo.Reals,
    )
    model.travel_cost = pyo.Param(
        model.N,
        model.N,
        initialize=lambda mdl, i, j: cost_matrix[i][j],
        within=pyo.Reals,
    )

    model.x = pyo.Var(model.A, domain=pyo.Binary)
    model.u = pyo.Var(
        model.T,
        domain=pyo.Reals,
        bounds=(1, n_nodes - 1),
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

    model.subtour_elimination = pyo.Constraint(
        model.T,
        model.T,
        rule=subtour_rule,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.travel_cost[i, j] * model.x[i, j]
            for i, j in model.A
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # Appsi raises this when it cannot load a feasible solution.
        if "feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}