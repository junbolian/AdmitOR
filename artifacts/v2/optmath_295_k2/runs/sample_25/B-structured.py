# IR: {"sets":{"V":"{0,...,n_cities-1}, with n_cities frozen at 4","A":"{(i,j) in V x V: i != j}","W":"V excluding 0"},"params":["cost_0_1","cost_0_2","cost_0_3","cost_1_0","cost_1_2","cost_1_3","cost_2_0","cost_2_1","cost_2_3","cost_3_0","cost_3_1","cost_3_2","n_cities","position_city_0","position_lower_bound","position_upper_bound","mtz_big_M","mtz_rhs"],"variables":{"x[i,j]":"Binary, (i,j) in A","u[i]":"Integer, i in V"},"constraints":["u[0] = position_city_0","position_lower_bound <= u[i] <= position_upper_bound for i in W","sum(x[i,j] for j in V if j != i) = 1 for i in V","sum(x[i,j] for i in V if i != j) = 1 for j in V","mtz_big_M*x[i,j] + u[i] - u[j] <= mtz_rhs for i,j in W with i != j"],"objective":"minimize sum(cost_i_j*x[i,j] for (i,j) in A)"}

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

    if position_lower_bound > position_upper_bound:
        return {"objective": None, "status": "infeasible_bounds"}

    model = pyo.ConcreteModel()

    model.city_count = pyo.Param(
        initialize=n_cities, within=pyo.PositiveIntegers
    )
    model.cities = pyo.RangeSet(0, int(pyo.value(model.city_count)) - 1)
    model.other_cities = pyo.Set(
        initialize=[city for city in model.cities if city != 0],
        within=model.cities,
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

    model.travel_cost = pyo.Param(
        model.arcs, initialize=costs, within=pyo.Reals
    )
    model.depot_position = pyo.Param(
        initialize=position_city_0, within=pyo.Reals
    )
    model.position_lb = pyo.Param(
        initialize=position_lower_bound, within=pyo.Reals
    )
    model.position_ub = pyo.Param(
        initialize=position_upper_bound, within=pyo.Reals
    )
    model.mtz_coefficient = pyo.Param(
        initialize=mtz_big_M, within=pyo.Reals
    )
    model.mtz_limit = pyo.Param(
        initialize=mtz_rhs, within=pyo.Reals
    )

    model.x = pyo.Var(model.arcs, domain=pyo.Binary)

    def position_bounds(mdl, city):
        if city == 0:
            return (None, None)
        return (mdl.position_lb, mdl.position_ub)

    model.u = pyo.Var(
        model.cities, domain=pyo.Integers, bounds=position_bounds
    )

    model.depot_position_constraint = pyo.Constraint(
        expr=model.u[0] == model.depot_position
    )

    def outgoing_rule(mdl, origin):
        return sum(
            mdl.x[origin, destination]
            for destination in mdl.cities
            if destination != origin
        ) == 1

    model.outgoing_constraints = pyo.Constraint(
        model.cities, rule=outgoing_rule
    )

    def incoming_rule(mdl, destination):
        return sum(
            mdl.x[origin, destination]
            for origin in mdl.cities
            if origin != destination
        ) == 1

    model.incoming_constraints = pyo.Constraint(
        model.cities, rule=incoming_rule
    )

    def mtz_rule(mdl, origin, destination):
        if origin == destination:
            return pyo.Constraint.Skip
        return (
            mdl.mtz_coefficient * mdl.x[origin, destination]
            + mdl.u[origin]
            - mdl.u[destination]
            <= mdl.mtz_limit
        )

    model.mtz_constraints = pyo.Constraint(
        model.other_cities, model.other_cities, rule=mtz_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.travel_cost[origin, destination]
            * model.x[origin, destination]
            for origin, destination in model.arcs
        ),
        sense=pyo.minimize,
    )

    # APPsi can raise RuntimeError when no solution can be loaded.
    # Objective retrieval is the sole success test.
    try:
        Highs().solve(model)
    except RuntimeError:
        pass

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "no_objective"}

    return {"objective": obj_val, "status": "optimal"}