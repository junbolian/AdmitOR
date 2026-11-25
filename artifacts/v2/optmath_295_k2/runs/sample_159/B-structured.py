# IR: {"sets":{"cities":[0,1,2,3,4],"nonroot":[1,2,3,4],"arcs":"(i,j) in cities x cities with i != j","position_arcs":"(i,j) in nonroot x nonroot with i != j"},"params":{"cost":"real-valued cost[i,j] read from params['cost_i_j'] for every arc"},"variables":{"x[i,j]":{"index":"arcs","type":"binary"},"position[i]":{"index":"nonroot","type":"integer","bounds":[1,4]}},"constraints":["departure[i]: sum(x[i,j] for j != i) == 1 for every city i","arrival[j]: sum(x[i,j] for i != j) == 1 for every city j","subtour[i,j]: position[i] - position[j] + 4*x[i,j] <= 3 for every position_arc (i,j); together with the degree constraints this yields distinct positions and one continuous loop"],"objective":{"sense":"minimize","expression":"sum(cost[i,j]*x[i,j] for (i,j) in arcs)"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cities = tuple(range(5))
    nonroot = tuple(range(1, 5))
    arcs = tuple(
        (origin, destination)
        for origin in cities
        for destination in cities
        if origin != destination
    )
    position_arcs = tuple(
        (origin, destination)
        for origin in nonroot
        for destination in nonroot
        if origin != destination
    )

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
    model.cities = pyo.Set(initialize=cities, ordered=True)
    model.nonroot = pyo.Set(initialize=nonroot, ordered=True)
    model.arcs = pyo.Set(initialize=arcs, dimen=2)
    model.position_arcs = pyo.Set(initialize=position_arcs, dimen=2)

    model.cost = pyo.Param(
        model.arcs,
        initialize=costs,
        within=pyo.Reals,
    )
    model.x = pyo.Var(model.arcs, domain=pyo.Binary)
    model.position = pyo.Var(
        model.nonroot,
        domain=pyo.Integers,
        bounds=(1, 4),
    )

    def departure_rule(instance, origin):
        return sum(
            instance.x[origin, destination]
            for destination in instance.cities
            if destination != origin
        ) == 1

    model.departure = pyo.Constraint(
        model.cities,
        rule=departure_rule,
    )

    def arrival_rule(instance, destination):
        return sum(
            instance.x[origin, destination]
            for origin in instance.cities
            if origin != destination
        ) == 1

    model.arrival = pyo.Constraint(
        model.cities,
        rule=arrival_rule,
    )

    def subtour_rule(instance, origin, destination):
        return (
            instance.position[origin]
            - instance.position[destination]
            + 4 * instance.x[origin, destination]
            <= 3
        )

    model.subtour = pyo.Constraint(
        model.position_arcs,
        rule=subtour_rule,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost[origin, destination] * model.x[origin, destination]
            for origin, destination in model.arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}