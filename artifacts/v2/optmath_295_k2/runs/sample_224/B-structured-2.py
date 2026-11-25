# IR: {"sets":{"C":[0,1,2,3,4,5],"A":"{(i,j) in C x C: i != j}","N":"C minus {0}"},"params":{"cost[i,j]":"params[f'cost_{i}_{j}'] for (i,j) in A","L":"params['pos_lower_bound']","U":"params['pos_upper_bound']","p0":"params['pos_0_fixed']","s":"params['subtour_separation_min']","M":"U-L+s (derived)"},"variables":{"route[i,j]":"binary for (i,j) in A","position[i]":"continuous in [L,U] for i in C"},"constraints":["sum(route[i,j] for j in C if j != i) = 1 for i in C","sum(route[i,j] for i in C if i != j) = 1 for j in C","position[0] = p0","position[i]-position[j] <= -s+M*(1-route[i,j]) for distinct i,j in N"],"objective":"minimize sum(cost[i,j]*route[i,j] for (i,j) in A)"}

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
    nondepot_cities = tuple(city for city in cities if city != 0)

    costs = {
        (origin, destination): params[f"cost_{origin}_{destination}"]
        for origin, destination in arcs
    }
    lower_bound = params["pos_lower_bound"]
    upper_bound = params["pos_upper_bound"]
    depot_position = params["pos_0_fixed"]
    separation = params["subtour_separation_min"]
    big_m = upper_bound - lower_bound + separation

    model = pyo.ConcreteModel()
    model.cities = pyo.Set(initialize=cities, ordered=True)
    model.arcs = pyo.Set(dimen=2, initialize=arcs, ordered=True)
    model.nondepot_cities = pyo.Set(
        initialize=nondepot_cities, ordered=True
    )

    model.travel_cost = pyo.Param(
        model.arcs, initialize=costs, within=pyo.Reals
    )
    model.route = pyo.Var(model.arcs, domain=pyo.Binary)
    model.position = pyo.Var(
        model.cities,
        domain=pyo.Reals,
        bounds=(lower_bound, upper_bound),
    )

    def outgoing_rule(instance, origin):
        return sum(
            instance.route[origin, destination]
            for destination in instance.cities
            if destination != origin
        ) == 1

    def incoming_rule(instance, destination):
        return sum(
            instance.route[origin, destination]
            for origin in instance.cities
            if origin != destination
        ) == 1

    model.outgoing_routes = pyo.Constraint(
        model.cities, rule=outgoing_rule
    )
    model.incoming_routes = pyo.Constraint(
        model.cities, rule=incoming_rule
    )
    model.depot_position_constraint = pyo.Constraint(
        expr=model.position[0] == depot_position
    )

    def subtour_rule(instance, origin, destination):
        if origin == destination:
            return pyo.Constraint.Skip
        return (
            instance.position[origin] - instance.position[destination]
            <= -separation
            + big_m * (1 - instance.route[origin, destination])
        )

    model.subtour_constraints = pyo.Constraint(
        model.nondepot_cities,
        model.nondepot_cities,
        rule=subtour_rule,
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
        # APPsi raises this error when it cannot load a feasible solution.
        # Continue to objective evaluation as the sole success test.
        if "A feasible solution was not found" not in str(exc):
            raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "no_objective"}

    return {"objective": obj_val, "status": "optimal"}