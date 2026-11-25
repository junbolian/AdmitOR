# IR: {"sets":{"cities":[0,1,2,3],"nondepot":[1,2,3],"arcs":"(i,j) in cities x cities where i != j","mtz_pairs":"(i,j) in nondepot x nondepot where i != j"},"params":["cost_0_1","cost_0_2","cost_0_3","cost_1_0","cost_1_2","cost_1_3","cost_2_0","cost_2_1","cost_2_3","cost_3_0","cost_3_1","cost_3_2","position_city_0","position_lower_bound","position_upper_bound","num_cities"],"variables":{"route[i,j]":"binary for (i,j) in arcs","position[i]":"real for i in cities"},"constraints":["sum(route[i,j] for j != i) = 1 for each city i","sum(route[i,j] for i != j) = 1 for each city j","position[0] = position_city_0","position_lower_bound <= position[i] <= position_upper_bound for i in nondepot","position[i] - position[j] + num_cities*route[i,j] <= num_cities - 1 for (i,j) in mtz_pairs"],"objective":{"sense":"minimize","expression":"sum(cost_i_j * route[i,j] for (i,j) in arcs)"}}

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
    model.nondepot = pyo.Set(initialize=[1, 2, 3], ordered=True)
    model.arcs = pyo.Set(
        dimen=2,
        initialize=[
            (i, j)
            for i in model.cities
            for j in model.cities
            if i != j
        ],
    )
    model.mtz_pairs = pyo.Set(
        dimen=2,
        initialize=[
            (i, j)
            for i in model.nondepot
            for j in model.nondepot
            if i != j
        ],
    )

    model.delivery_cost = pyo.Param(model.arcs, initialize=costs)
    model.depot_position = pyo.Param(
        initialize=params["position_city_0"]
    )
    model.position_lb = pyo.Param(
        initialize=params["position_lower_bound"]
    )
    model.position_ub = pyo.Param(
        initialize=params["position_upper_bound"]
    )
    model.city_count = pyo.Param(initialize=params["num_cities"])

    model.route = pyo.Var(model.arcs, domain=pyo.Binary)
    model.position = pyo.Var(model.cities, domain=pyo.Reals)

    def departure_rule(mdl, i):
        return sum(
            mdl.route[i, j] for j in mdl.cities if j != i
        ) == 1

    model.departure_once = pyo.Constraint(
        model.cities, rule=departure_rule
    )

    def arrival_rule(mdl, j):
        return sum(
            mdl.route[i, j] for i in mdl.cities if i != j
        ) == 1

    model.arrival_once = pyo.Constraint(
        model.cities, rule=arrival_rule
    )

    model.fixed_depot_position = pyo.Constraint(
        expr=model.position[0] == model.depot_position
    )

    def position_bounds_rule(mdl, i):
        return (
            mdl.position_lb,
            mdl.position[i],
            mdl.position_ub,
        )

    model.sequence_bounds = pyo.Constraint(
        model.nondepot, rule=position_bounds_rule
    )

    def subtour_rule(mdl, i, j):
        return (
            mdl.position[i]
            - mdl.position[j]
            + mdl.city_count * mdl.route[i, j]
            <= mdl.city_count - 1
        )

    model.subtour_elimination = pyo.Constraint(
        model.mtz_pairs, rule=subtour_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.delivery_cost[i, j] * model.route[i, j]
            for i, j in model.arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}