# IR: {"sets":{"V":"1..n","A":"{(i,j) in V x V: i != j}","U":"V excluding depot 1"},"params":{"n":"params['num_customers']","d":"params['distance_matrix'], a square zero-based matrix"},"variables":{"x[i,j]":"Binary for (i,j) in A","u[i]":"Real in [1,n-1] for i in U"},"constraints":["For each i in V: sum(x[i,j] for j in V if j != i) = 1","For each j in V: sum(x[i,j] for i in V if i != j) = 1","For distinct i,j in U: u[i] - u[j] + n*x[i,j] <= n-1"],"objective":"Minimize sum(d[i-1][j-1]*x[i,j] for (i,j) in A)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve the symmetric TSP, with location 1 as the depot."""
    n = params["num_customers"]
    distance_matrix = params["distance_matrix"]

    model = pyo.ConcreteModel()

    model.locations = pyo.RangeSet(1, n)
    model.non_depot_locations = pyo.Set(
        initialize=[i for i in range(1, n + 1) if i != 1],
        ordered=True,
    )
    model.arcs = pyo.Set(
        dimen=2,
        initialize=[
            (i, j)
            for i in range(1, n + 1)
            for j in range(1, n + 1)
            if i != j
        ],
    )

    model.travel_distance = pyo.Param(
        model.arcs,
        initialize={
            (i, j): distance_matrix[i - 1][j - 1]
            for i, j in model.arcs
        },
        within=pyo.Reals,
    )

    model.x = pyo.Var(model.arcs, domain=pyo.Binary)
    model.u = pyo.Var(
        model.non_depot_locations,
        domain=pyo.Reals,
        bounds=(1, n - 1),
    )

    def outgoing_rule(instance, i):
        return sum(
            instance.x[i, j]
            for j in instance.locations
            if j != i
        ) == 1

    model.outgoing_degree = pyo.Constraint(
        model.locations, rule=outgoing_rule
    )

    def incoming_rule(instance, j):
        return sum(
            instance.x[i, j]
            for i in instance.locations
            if i != j
        ) == 1

    model.incoming_degree = pyo.Constraint(
        model.locations, rule=incoming_rule
    )

    def subtour_rule(instance, i, j):
        if i == j:
            return pyo.Constraint.Skip
        return (
            instance.u[i] - instance.u[j] + n * instance.x[i, j]
            <= n - 1
        )

    model.subtour_elimination = pyo.Constraint(
        model.non_depot_locations,
        model.non_depot_locations,
        rule=subtour_rule,
    )

    model.total_distance = pyo.Objective(
        expr=sum(
            model.travel_distance[i, j] * model.x[i, j]
            for i, j in model.arcs
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
        obj_val = float(pyo.value(model.total_distance))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}