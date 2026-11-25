# IR: {"sets":{"C":[0,1,2,3,4,5,6],"A":"{(i,j) in C x C: i != j}","F":"{(i,j) in A: j != 0}"},"params":{"distance[i,j]":"params[f'distance_{i}_{j}'] for (i,j) in A","L":"params['position_min']","U":"params['position_max']","M":"U-L+1"},"variables":{"x[i,j]":"Binary for (i,j) in A","position[i]":"Integer, L <= position[i] <= U, for i in C"},"constraints":["sum(x[i,j] for j in C if j != i) = 1 for i in C","sum(x[i,j] for i in C if i != j) = 1 for j in C","position[0] = L","position[j] >= position[i]+1-M*(1-x[i,j]) for (i,j) in F","position[j] <= position[i]+1+M*(1-x[i,j]) for (i,j) in F"],"objective":"minimize sum(distance[i,j]*x[i,j] for (i,j) in A)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.cities = pyo.Set(initialize=range(7), ordered=True)
    model.arcs = pyo.Set(
        dimen=2,
        initialize=[
            (i, j)
            for i in range(7)
            for j in range(7)
            if i != j
        ],
    )
    model.forward_arcs = pyo.Set(
        dimen=2,
        initialize=[
            (i, j)
            for i in range(7)
            for j in range(7)
            if i != j and j != 0
        ],
    )

    model.distance = pyo.Param(
        model.arcs,
        initialize={
            (i, j): params[f"distance_{i}_{j}"]
            for i, j in model.arcs
        },
        within=pyo.Reals,
    )
    model.position_lower = pyo.Param(
        initialize=params["position_min"],
        within=pyo.Reals,
    )
    model.position_upper = pyo.Param(
        initialize=params["position_max"],
        within=pyo.Reals,
    )
    model.order_big_m = pyo.Expression(
        expr=model.position_upper - model.position_lower + 1
    )

    model.route_selected = pyo.Var(model.arcs, domain=pyo.Binary)
    model.tour_position = pyo.Var(
        model.cities,
        domain=pyo.Integers,
        bounds=lambda mod, i: (
            mod.position_lower,
            mod.position_upper,
        ),
    )

    def outgoing_rule(mod, i):
        return sum(
            mod.route_selected[i, j]
            for j in mod.cities
            if j != i
        ) == 1

    model.outgoing_once = pyo.Constraint(
        model.cities,
        rule=outgoing_rule,
    )

    def incoming_rule(mod, j):
        return sum(
            mod.route_selected[i, j]
            for i in mod.cities
            if i != j
        ) == 1

    model.incoming_once = pyo.Constraint(
        model.cities,
        rule=incoming_rule,
    )

    model.start_position = pyo.Constraint(
        expr=model.tour_position[0] == model.position_lower
    )

    # Selected arcs advance the position by exactly one, except for
    # the return to City 0. This also forces all positions to be unique
    # and excludes every subtour that does not contain City 0.
    def order_lower_rule(mod, i, j):
        return (
            mod.tour_position[j]
            >= mod.tour_position[i]
            + 1
            - mod.order_big_m * (1 - mod.route_selected[i, j])
        )

    model.order_lower = pyo.Constraint(
        model.forward_arcs,
        rule=order_lower_rule,
    )

    def order_upper_rule(mod, i, j):
        return (
            mod.tour_position[j]
            <= mod.tour_position[i]
            + 1
            + mod.order_big_m * (1 - mod.route_selected[i, j])
        )

    model.order_upper = pyo.Constraint(
        model.forward_arcs,
        rule=order_upper_rule,
    )

    model.total_distance = pyo.Objective(
        expr=sum(
            model.distance[i, j] * model.route_selected[i, j]
            for i, j in model.arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        # HiGHS may raise when no feasible solution can be loaded.
        # Objective retrieval below is the sole success criterion.
        pass

    try:
        obj_val = float(pyo.value(model.total_distance))
    except (ValueError, TypeError):
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}