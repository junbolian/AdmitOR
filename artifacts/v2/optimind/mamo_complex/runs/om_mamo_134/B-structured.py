# IR: {"sets":{"V":"range(n)","A":"{(i,j) in V x V: i != j}","U":"V \\ {0}"},"params":{"n":"params['n']","cost":"params['cost'], symmetric matrix indexed from 0"},"variables":{"x[i,j]":"Binary for (i,j) in A","u[i]":"Real in [1,n-1] for i in U"},"constraints":["For each i in V: sum(x[i,j] for j in V if j != i) = 1","For each j in V: sum(x[i,j] for i in V if i != j) = 1","For distinct i,j in U: u[i] - u[j] + n*x[i,j] <= n-1"],"objective":"Minimize sum(cost[i][j]*x[i,j] for (i,j) in A)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    n = params["n"]
    cost = params["cost"]

    model = pyo.ConcreteModel()

    model.cities = pyo.Set(initialize=range(n), ordered=True)
    model.arcs = pyo.Set(
        dimen=2,
        initialize=[
            (i, j)
            for i in range(n)
            for j in range(n)
            if i != j
        ],
    )
    model.non_depot = pyo.Set(initialize=range(1, n), ordered=True)

    model.travel = pyo.Var(model.arcs, domain=pyo.Binary)
    model.visit_order = pyo.Var(
        model.non_depot,
        domain=pyo.Reals,
        bounds=(1, n - 1),
    )

    def outgoing_rule(problem, i):
        return sum(
            problem.travel[i, j]
            for j in problem.cities
            if j != i
        ) == 1

    model.outgoing = pyo.Constraint(model.cities, rule=outgoing_rule)

    def incoming_rule(problem, j):
        return sum(
            problem.travel[i, j]
            for i in problem.cities
            if i != j
        ) == 1

    model.incoming = pyo.Constraint(model.cities, rule=incoming_rule)

    def subtour_rule(problem, i, j):
        if i == j:
            return pyo.Constraint.Skip
        return (
            problem.visit_order[i]
            - problem.visit_order[j]
            + n * problem.travel[i, j]
            <= n - 1
        )

    model.subtour_elimination = pyo.Constraint(
        model.non_depot,
        model.non_depot,
        rule=subtour_rule,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            cost[i][j] * model.travel[i, j]
            for i, j in model.arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}