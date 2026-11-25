# IR: {"sets":{"C":"{0,...,n_cities-1}, with n_cities frozen at 4","A":"{(i,j) in C x C: i != j}","N":"C excluding 0","T":"{(i,j) in N x N: i != j}"},"params":["cost_0_1","cost_0_2","cost_0_3","cost_1_0","cost_1_2","cost_1_3","cost_2_0","cost_2_1","cost_2_3","cost_3_0","cost_3_1","cost_3_2","n_cities","position_city_0","position_lower_bound","position_upper_bound","mtz_big_M","mtz_rhs"],"variables":{"x[i,j]":"binary for (i,j) in A","u[i]":"integer for i in C"},"constraints":["sum(x[i,j] for j in C if j != i) = 1 for each i in C","sum(x[i,j] for i in C if i != j) = 1 for each j in C","u[0] = position_city_0","position_lower_bound <= u[i] <= position_upper_bound for each i in N","mtz_big_M*x[i,j] + u[i] - u[j] <= mtz_rhs for each (i,j) in T"],"objective":"minimize sum(cost[i,j]*x[i,j] for (i,j) in A)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    n_cities = params["n_cities"]

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

    position_city_0 = params["position_city_0"]
    position_lower_bound = params["position_lower_bound"]
    position_upper_bound = params["position_upper_bound"]
    mtz_big_M = params["mtz_big_M"]
    mtz_rhs = params["mtz_rhs"]

    if n_cities != 4:
        return {"objective": None, "status": "invalid_n_cities"}

    model = pyo.ConcreteModel()

    model.cities = pyo.RangeSet(0, int(n_cities) - 1)
    model.non_depot_cities = pyo.Set(
        initialize=[city for city in model.cities if city != 0]
    )
    model.arcs = pyo.Set(
        dimen=2,
        initialize=[
            (origin, destination)
            for origin in model.cities
            for destination in model.cities
            if origin != destination
        ],
    )
    model.mtz_arcs = pyo.Set(
        dimen=2,
        initialize=[
            (origin, destination)
            for origin in model.non_depot_cities
            for destination in model.non_depot_cities
            if origin != destination
        ],
    )

    model.travel_cost = pyo.Param(model.arcs, initialize=costs)
    model.mtz_coefficient = pyo.Param(initialize=mtz_big_M)
    model.mtz_limit = pyo.Param(initialize=mtz_rhs)

    model.x = pyo.Var(model.arcs, domain=pyo.Binary)
    model.u = pyo.Var(model.cities, domain=pyo.Integers)

    model.u[0].fix(position_city_0)
    for city in model.non_depot_cities:
        model.u[city].setlb(position_lower_bound)
        model.u[city].setub(position_upper_bound)

    def outgoing_rule(instance, origin):
        return sum(
            instance.x[origin, destination]
            for destination in instance.cities
            if destination != origin
        ) == 1

    def incoming_rule(instance, destination):
        return sum(
            instance.x[origin, destination]
            for origin in instance.cities
            if origin != destination
        ) == 1

    def mtz_rule(instance, origin, destination):
        return (
            instance.mtz_coefficient * instance.x[origin, destination]
            + instance.u[origin]
            - instance.u[destination]
            <= instance.mtz_limit
        )

    model.outgoing_degree = pyo.Constraint(
        model.cities, rule=outgoing_rule
    )
    model.incoming_degree = pyo.Constraint(
        model.cities, rule=incoming_rule
    )
    model.subtour_elimination = pyo.Constraint(
        model.mtz_arcs, rule=mtz_rule
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
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}