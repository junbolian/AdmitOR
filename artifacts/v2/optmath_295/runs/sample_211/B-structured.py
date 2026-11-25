# IR: {"sets":{"V":[0,1,2,3,4],"A":"{(i,j): i,j in V, i != j}","U":[1,2,3,4]},"params":["cost_0_1","cost_0_2","cost_0_3","cost_0_4","cost_1_0","cost_1_2","cost_1_3","cost_1_4","cost_2_0","cost_2_1","cost_2_3","cost_2_4","cost_3_0","cost_3_1","cost_3_2","cost_3_4","cost_4_0","cost_4_1","cost_4_2","cost_4_3"],"variables":{"x[i,j]":"binary for (i,j) in A","u[i]":"integer in [0,4] for i in V"},"constraints":["sum(x[i,j] for j in V if j != i) = 1 for i in V","sum(x[i,j] for i in V if i != j) = 1 for j in V","u[0] = 0","u[i] >= 1 for i in U","u[i] - u[j] + 5*x[i,j] <= 4 for i,j in U with i != j"],"objective":"minimize sum(cost_i_j*x[i,j] for (i,j) in A)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    costs = {
        (0, 1): params["cost_0_1"],
        (0, 2): params["cost_0_2"],
        (0, 3): params["cost_0_3"],
        (0, 4): params["cost_0_4"],
        (1, 0): params["cost_1_0"],
        (1, 2): params["cost_1_2"],
        (1, 3): params["cost_1_3"],
        (1, 4): params["cost_1_4"],
        (2, 0): params["cost_2_0"],
        (2, 1): params["cost_2_1"],
        (2, 3): params["cost_2_3"],
        (2, 4): params["cost_2_4"],
        (3, 0): params["cost_3_0"],
        (3, 1): params["cost_3_1"],
        (3, 2): params["cost_3_2"],
        (3, 4): params["cost_3_4"],
        (4, 0): params["cost_4_0"],
        (4, 1): params["cost_4_1"],
        (4, 2): params["cost_4_2"],
        (4, 3): params["cost_4_3"],
    }

    model = pyo.ConcreteModel()
    model.V = pyo.Set(initialize=range(5), ordered=True)
    model.A = pyo.Set(
        dimen=2,
        initialize=[
            (origin, destination)
            for origin in range(5)
            for destination in range(5)
            if origin != destination
        ],
    )
    model.U = pyo.Set(initialize=range(1, 5), ordered=True)
    model.cost = pyo.Param(model.A, initialize=costs, within=pyo.Reals)

    model.x = pyo.Var(model.A, domain=pyo.Binary)
    model.u = pyo.Var(model.V, domain=pyo.Integers, bounds=(0, 4))

    def departure_rule(instance, origin):
        return sum(
            instance.x[origin, destination]
            for destination in instance.V
            if destination != origin
        ) == 1

    model.departure = pyo.Constraint(model.V, rule=departure_rule)

    def arrival_rule(instance, destination):
        return sum(
            instance.x[origin, destination]
            for origin in instance.V
            if origin != destination
        ) == 1

    model.arrival = pyo.Constraint(model.V, rule=arrival_rule)
    model.depot_position = pyo.Constraint(expr=model.u[0] == 0)
    model.non_depot_position = pyo.Constraint(
        model.U,
        rule=lambda instance, city: instance.u[city] >= 1,
    )

    def subtour_rule(instance, origin, destination):
        if origin == destination:
            return pyo.Constraint.Skip
        return (
            instance.u[origin]
            - instance.u[destination]
            + 5 * instance.x[origin, destination]
            <= 4
        )

    model.subtour = pyo.Constraint(model.U, model.U, rule=subtour_rule)

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost[origin, destination] * model.x[origin, destination]
            for origin, destination in model.A
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