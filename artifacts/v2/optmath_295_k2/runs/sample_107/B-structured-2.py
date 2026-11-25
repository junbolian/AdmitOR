# IR: {"sets":{"cities":[0,1,2,3],"nondepot":[1,2,3],"arcs":"(i,j) in cities^2 where i != j","mtz_pairs":"(i,j) in nondepot^2 where i != j"},"params":{"cost_0_1":"params['cost_0_1']","cost_0_2":"params['cost_0_2']","cost_0_3":"params['cost_0_3']","cost_1_0":"params['cost_1_0']","cost_1_2":"params['cost_1_2']","cost_1_3":"params['cost_1_3']","cost_2_0":"params['cost_2_0']","cost_2_1":"params['cost_2_1']","cost_2_3":"params['cost_2_3']","cost_3_0":"params['cost_3_0']","cost_3_1":"params['cost_3_1']","cost_3_2":"params['cost_3_2']","position_city_0":"params['position_city_0']","position_lower_bound":"params['position_lower_bound']","position_upper_bound":"params['position_upper_bound']","num_cities":"params['num_cities']"},"variables":{"x[i,j]":"Binary for each arc","u[i]":"Real for each city"},"constraints":["sum(x[i,j] for j != i) = 1 for each city i","sum(x[i,j] for i != j) = 1 for each city j","u[0] = position_city_0","position_lower_bound <= u[i] <= position_upper_bound for each nondepot city i","u[i] - u[j] + num_cities*x[i,j] <= num_cities - 1 for each mtz_pair"],"objective":"minimize sum(cost_i_j*x[i,j] for each arc)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.cities = pyo.Set(initialize=[0, 1, 2, 3], ordered=True)
    model.nondepot = pyo.Set(initialize=[1, 2, 3], ordered=True)
    model.arcs = pyo.Set(
        dimen=2,
        initialize=[
            (origin, destination)
            for origin in model.cities
            for destination in model.cities
            if origin != destination
        ],
    )
    model.mtz_pairs = pyo.Set(
        dimen=2,
        initialize=[
            (origin, destination)
            for origin in model.nondepot
            for destination in model.nondepot
            if origin != destination
        ],
    )

    model.travel_cost = pyo.Param(
        model.arcs,
        initialize={
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
        },
        within=pyo.Reals,
    )
    model.depot_position = pyo.Param(
        initialize=params["position_city_0"], within=pyo.Reals
    )
    model.position_lb = pyo.Param(
        initialize=params["position_lower_bound"], within=pyo.Reals
    )
    model.position_ub = pyo.Param(
        initialize=params["position_upper_bound"], within=pyo.Reals
    )
    model.city_count = pyo.Param(
        initialize=params["num_cities"], within=pyo.Reals
    )

    model.x = pyo.Var(model.arcs, domain=pyo.Binary)
    model.u = pyo.Var(model.cities, domain=pyo.Reals)

    def departure_rule(instance, origin):
        return sum(
            instance.x[origin, destination]
            for destination in instance.cities
            if destination != origin
        ) == 1

    model.departure_once = pyo.Constraint(
        model.cities, rule=departure_rule
    )

    def arrival_rule(instance, destination):
        return sum(
            instance.x[origin, destination]
            for origin in instance.cities
            if origin != destination
        ) == 1

    model.arrival_once = pyo.Constraint(
        model.cities, rule=arrival_rule
    )

    model.depot_position_constraint = pyo.Constraint(
        expr=model.u[0] == model.depot_position
    )

    def position_bounds_rule(instance, city):
        return (
            instance.position_lb,
            instance.u[city],
            instance.position_ub,
        )

    model.position_bounds = pyo.Constraint(
        model.nondepot, rule=position_bounds_rule
    )

    def subtour_rule(instance, origin, destination):
        return (
            instance.u[origin]
            - instance.u[destination]
            + instance.city_count * instance.x[origin, destination]
            <= instance.city_count - 1
        )

    model.subtour_elimination = pyo.Constraint(
        model.mtz_pairs, rule=subtour_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.travel_cost[origin, destination]
            * model.x[origin, destination]
            for origin, destination in model.arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        # HiGHS can raise when no feasible solution can be loaded.
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}