# IR: {"sets":{"C":[0,1,2,3,4,5],"A":"{(i,j): i,j in C, i != j}","F":"{(i,j) in A: j != 0}"},"params":{"cost_i_j":"params['cost_i_j'] for each (i,j) in A","L":"params['pos_lower_bound']","U":"params['pos_upper_bound']","p0":"params['pos_0_fixed']","d":"params['subtour_separation_min']","M":"U-L+d (derived)"},"variables":{"x[i,j]":"Binary for (i,j) in A","pos[i]":"Real in [L,U] for i in C"},"constraints":["sum(x[i,j] for j in C if j != i) = 1 for i in C","sum(x[i,j] for i in C if i != j) = 1 for j in C","pos[0] = p0","pos[i]-pos[j] <= -d + M*(1-x[i,j]) for (i,j) in F"],"objective":"minimize sum(cost_i_j*x[i,j] for (i,j) in A)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cities = tuple(range(6))
    arcs = tuple(
        (origin, destination)
        for origin in cities
        for destination in cities
        if origin != destination
    )
    forward_arcs = tuple(
        (origin, destination)
        for origin, destination in arcs
        if destination != 0
    )

    costs = {
        (origin, destination): params[f"cost_{origin}_{destination}"]
        for origin, destination in arcs
    }
    lower_bound = params["pos_lower_bound"]
    upper_bound = params["pos_upper_bound"]
    depot_position = params["pos_0_fixed"]
    separation = params["subtour_separation_min"]

    model = pyo.ConcreteModel()

    model.cities = pyo.Set(initialize=cities, ordered=True)
    model.arcs = pyo.Set(dimen=2, initialize=arcs, ordered=True)
    model.forward_arcs = pyo.Set(
        dimen=2, initialize=forward_arcs, ordered=True
    )

    model.travel_cost = pyo.Param(model.arcs, initialize=costs)
    model.position_lower = pyo.Param(initialize=lower_bound)
    model.position_upper = pyo.Param(initialize=upper_bound)
    model.depot_position = pyo.Param(initialize=depot_position)
    model.separation = pyo.Param(initialize=separation)
    model.big_m = pyo.Expression(
        expr=model.position_upper - model.position_lower + model.separation
    )

    model.route = pyo.Var(model.arcs, domain=pyo.Binary)
    model.position = pyo.Var(
        model.cities,
        domain=pyo.Reals,
        bounds=(model.position_lower, model.position_upper),
    )

    def outgoing_rule(instance, origin):
        return sum(
            instance.route[origin, destination]
            for destination in instance.cities
            if destination != origin
        ) == 1

    model.outgoing_route = pyo.Constraint(
        model.cities, rule=outgoing_rule
    )

    def incoming_rule(instance, destination):
        return sum(
            instance.route[origin, destination]
            for origin in instance.cities
            if origin != destination
        ) == 1

    model.incoming_route = pyo.Constraint(
        model.cities, rule=incoming_rule
    )

    model.depot_anchor = pyo.Constraint(
        expr=model.position[0] == model.depot_position
    )

    def subtour_rule(instance, origin, destination):
        return (
            instance.position[origin] - instance.position[destination]
            <= -instance.separation
            + instance.big_m * (1 - instance.route[origin, destination])
        )

    model.subtour_elimination = pyo.Constraint(
        model.forward_arcs, rule=subtour_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.travel_cost[origin, destination]
            * model.route[origin, destination]
            for origin, destination in model.arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPsi raises this when it cannot load a feasible solution.
        # Still determine success solely by objective retrieval below.
        if "A feasible solution was not found" not in str(exc):
            raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "no_solution"}

    return {"objective": obj_val, "status": "optimal"}