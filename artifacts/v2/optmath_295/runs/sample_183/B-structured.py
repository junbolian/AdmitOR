# IR: {"sets":{"V":[0,1,2,3,4,5,6,7],"W":"V excluding 0","A":"{(i,j) in V x V: i != j}"},"params":{"distance[i,j]":"params[f'dist_{i}_{j}'] for (i,j) in A"},"variables":{"x[i,j]":{"type":"binary","indices":"A"},"u[i]":{"type":"integer","indices":"V","bounds":[0,7]}},"constraints":["sum(x[i,j] for j in V if j != i) == 1 for i in V","sum(x[i,j] for i in V if i != j) == 1 for j in V","u[0] == 0","u[i] >= 1 for i in W","u[i] - u[j] + 8*x[i,j] <= 7 for i,j in W if i != j"],"objective":{"sense":"minimize","expression":"sum(distance[i,j]*x[i,j] for (i,j) in A)"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.cities = pyo.Set(initialize=range(8), ordered=True)
    model.nonroot_cities = pyo.Set(initialize=range(1, 8), ordered=True)
    model.arcs = pyo.Set(
        dimen=2,
        initialize=[
            (i, j)
            for i in range(8)
            for j in range(8)
            if i != j
        ],
    )

    model.distance = pyo.Param(
        model.arcs,
        initialize={
            (i, j): params[f"dist_{i}_{j}"]
            for i, j in model.arcs
        },
        within=pyo.Reals,
    )

    model.x = pyo.Var(model.arcs, domain=pyo.Binary)
    model.u = pyo.Var(model.cities, domain=pyo.Integers, bounds=(0, 7))

    def departure_rule(mod, i):
        return sum(
            mod.x[i, j] for j in mod.cities if j != i
        ) == 1

    model.departure_constraints = pyo.Constraint(
        model.cities, rule=departure_rule
    )

    def arrival_rule(mod, j):
        return sum(
            mod.x[i, j] for i in mod.cities if i != j
        ) == 1

    model.arrival_constraints = pyo.Constraint(
        model.cities, rule=arrival_rule
    )

    model.root_position_constraint = pyo.Constraint(expr=model.u[0] == 0)

    def nonroot_position_rule(mod, i):
        return mod.u[i] >= 1

    model.nonroot_position_constraints = pyo.Constraint(
        model.nonroot_cities, rule=nonroot_position_rule
    )

    def subtour_rule(mod, i, j):
        if i == j:
            return pyo.Constraint.Skip
        return mod.u[i] - mod.u[j] + 8 * mod.x[i, j] <= 7

    model.subtour_constraints = pyo.Constraint(
        model.nonroot_cities,
        model.nonroot_cities,
        rule=subtour_rule,
    )

    model.total_distance = pyo.Objective(
        expr=sum(
            model.distance[i, j] * model.x[i, j]
            for i, j in model.arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPsi raises this when no feasible solution can be loaded.
        # Unexpected solver errors still propagate.
        if "a feasible solution was not found" not in str(exc).lower():
            raise

    try:
        obj_val = float(pyo.value(model.total_distance))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}