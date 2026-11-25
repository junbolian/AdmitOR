# IR: {"sets":{"V":"{0,...,n-1}","U":"V\\{0}","A":"{(i,j) in VxV: i!=j}","D":"{0,1}"},"params":{"n":"params['num_checkpoints']","c[i,j]":"params['cost_matrix'][i][j]","coordinates[i,d]":"params['checkpoint_coordinates'][i][d] (metadata only)"},"variables":{"x[i,j]":"binary, (i,j) in A","u[i]":"continuous, 1<=u[i]<=n-1, i in U"},"constraints":["sum(x[i,j] for j in V if j!=i)=1 for i in V","sum(x[i,j] for i in V if i!=j)=1 for j in V","u[i]-u[j]+n*x[i,j]<=n-1 for distinct i,j in U"],"objective":"minimize sum(c[i,j]*x[i,j] for (i,j) in A)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    n = params["num_checkpoints"]
    cost_matrix = params["cost_matrix"]
    checkpoint_coordinates = params["checkpoint_coordinates"]

    model = pyo.ConcreteModel()

    model.checkpoints = pyo.Set(initialize=range(n), ordered=True)
    model.inspection_points = pyo.Set(initialize=range(1, n), ordered=True)
    model.dimensions = pyo.Set(initialize=(0, 1), ordered=True)
    model.arcs = pyo.Set(
        dimen=2,
        initialize=(
            (i, j)
            for i in range(n)
            for j in range(n)
            if i != j
        ),
        ordered=True,
    )

    model.transition_cost = pyo.Param(
        model.checkpoints,
        model.checkpoints,
        initialize=lambda mdl, i, j: cost_matrix[i][j],
        within=pyo.Reals,
    )
    model.coordinates = pyo.Param(
        model.checkpoints,
        model.dimensions,
        initialize=lambda mdl, i, d: checkpoint_coordinates[i][d],
        within=pyo.Reals,
    )

    model.x = pyo.Var(model.arcs, domain=pyo.Binary)
    model.u = pyo.Var(
        model.inspection_points,
        domain=pyo.Reals,
        bounds=(1, n - 1),
    )

    def outgoing_rule(mdl, i):
        return sum(
            mdl.x[i, j] for j in mdl.checkpoints if j != i
        ) == 1

    model.outgoing = pyo.Constraint(
        model.checkpoints, rule=outgoing_rule
    )

    def incoming_rule(mdl, j):
        return sum(
            mdl.x[i, j] for i in mdl.checkpoints if i != j
        ) == 1

    model.incoming = pyo.Constraint(
        model.checkpoints, rule=incoming_rule
    )

    def subtour_rule(mdl, i, j):
        if i == j:
            return pyo.Constraint.Skip
        return mdl.u[i] - mdl.u[j] + n * mdl.x[i, j] <= n - 1

    model.subtour_elimination = pyo.Constraint(
        model.inspection_points,
        model.inspection_points,
        rule=subtour_rule,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.transition_cost[i, j] * model.x[i, j]
            for i, j in model.arcs
        ),
        sense=pyo.minimize,
    )

    solver_failed = False
    try:
        Highs().solve(model)
    except RuntimeError:
        solver_failed = True

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {
            "objective": None,
            "status": "solve_failed" if solver_failed else "objective_unavailable",
        }

    return {"objective": obj_val, "status": "optimal"}