# IR: {"sets":{"V":[0,1,2,3],"N":[1,2,3],"A":"{(i,j) in V x V: i != j}"},"params":["cost_0_1","cost_0_2","cost_0_3","cost_1_0","cost_1_2","cost_1_3","cost_2_0","cost_2_1","cost_2_3","cost_3_0","cost_3_1","cost_3_2"],"variables":{"x[i,j]":"binary, (i,j) in A","u[i]":"continuous in [0,3], i in V"},"constraints":["sum(x[i,j] for j in V if j != i) = 1 for i in V","sum(x[i,j] for i in V if i != j) = 1 for j in V","u[0] = 0","u[i] - u[j] + 4*x[i,j] <= 3 for i,j in N with i != j"],"objective":"minimize sum(cost_i_j*x[i,j] for (i,j) in A)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    costs = {
        (0, 1): params["cost_0_1"],
        (0, 2): params["cost_0_2"],
        (0, 3): params["cost_0_3"],
        (1, 0): params["cost_1_0"],
        (1, 2): params["cost_1_2"],
        (1, 3): params["cost_1_3"],
        (2, 0): params["cost_2_0"],
        (2, 1): params["cost_2_1"],
        (2, 3): params["cost_2_3"],
        (3, 0): params["cost_3_0"],
        (3, 1): params["cost_3_1"],
        (3, 2): params["cost_3_2"],
    }

    model = pyo.ConcreteModel()

    model.cities = pyo.Set(initialize=[0, 1, 2, 3], ordered=True)
    model.nonroot_cities = pyo.Set(initialize=[1, 2, 3], ordered=True)
    model.arcs = pyo.Set(
        dimen=2,
        initialize=[
            (i, j)
            for i in model.cities
            for j in model.cities
            if i != j
        ],
    )
    model.nonroot_arcs = pyo.Set(
        dimen=2,
        initialize=[
            (i, j)
            for i in model.nonroot_cities
            for j in model.nonroot_cities
            if i != j
        ],
    )

    model.travel_cost = pyo.Param(
        model.arcs, initialize=costs, within=pyo.Reals
    )
    model.x = pyo.Var(model.arcs, domain=pyo.Binary)
    model.u = pyo.Var(model.cities, domain=pyo.Reals, bounds=(0, 3))

    def departure_rule(instance, i):
        return sum(
            instance.x[i, j] for j in instance.cities if j != i
        ) == 1

    model.departure_constraints = pyo.Constraint(
        model.cities, rule=departure_rule
    )

    def arrival_rule(instance, j):
        return sum(
            instance.x[i, j] for i in instance.cities if i != j
        ) == 1

    model.arrival_constraints = pyo.Constraint(
        model.cities, rule=arrival_rule
    )

    model.root_position = pyo.Constraint(expr=model.u[0] == 0)

    def subtour_rule(instance, i, j):
        return instance.u[i] - instance.u[j] + 4 * instance.x[i, j] <= 3

    model.subtour_constraints = pyo.Constraint(
        model.nonroot_arcs, rule=subtour_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.travel_cost[i, j] * model.x[i, j]
            for i, j in model.arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}