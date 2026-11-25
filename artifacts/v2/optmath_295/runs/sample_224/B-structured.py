# IR: {"sets":{"V":[0,1,2,3,4,5],"A":"{(i,j) in V x V: i != j}","W":"V \\ {0}"},"params":{"cost[i,j]":"params[f'cost_{i}_{j}'] for (i,j) in A","L":"params['position_bound_lower']","U":"params['position_bound_upper']","p0":"params['city0_position']"},"variables":{"x[i,j]":"Binary for (i,j) in A","u[i]":"Real, L <= u[i] <= U, for i in V"},"constraints":["sum(x[i,j] for j in V if j != i) = 1 for i in V","sum(x[i,j] for i in V if i != j) = 1 for j in V","u[0] = p0","u[i] - u[j] + (U-L+1)*x[i,j] <= U-L for distinct i,j in W"],"objective":"minimize sum(cost[i,j]*x[i,j] for (i,j) in A)"}

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

    travel_costs = {
        (origin, destination): params[f"cost_{origin}_{destination}"]
        for origin, destination in arcs
    }
    lower_bound = params["position_bound_lower"]
    upper_bound = params["position_bound_upper"]
    depot_position = params["city0_position"]

    model = pyo.ConcreteModel()

    model.cities = pyo.Set(initialize=cities, ordered=True)
    model.arcs = pyo.Set(initialize=arcs, dimen=2, ordered=True)
    model.nondepot_cities = pyo.Set(
        initialize=nondepot_cities, ordered=True
    )

    model.travel_cost = pyo.Param(
        model.arcs, initialize=travel_costs, within=pyo.Reals
    )
    model.position_lower = pyo.Param(
        initialize=lower_bound, within=pyo.Reals
    )
    model.position_upper = pyo.Param(
        initialize=upper_bound, within=pyo.Reals
    )
    model.depot_position = pyo.Param(
        initialize=depot_position, within=pyo.Reals
    )

    model.route = pyo.Var(model.arcs, domain=pyo.Binary)
    model.position = pyo.Var(
        model.cities,
        domain=pyo.Reals,
        bounds=(lower_bound, upper_bound),
    )

    def outgoing_rule(problem, origin):
        return sum(
            problem.route[origin, destination]
            for destination in problem.cities
            if destination != origin
        ) == 1

    def incoming_rule(problem, destination):
        return sum(
            problem.route[origin, destination]
            for origin in problem.cities
            if origin != destination
        ) == 1

    model.outgoing_routes = pyo.Constraint(
        model.cities, rule=outgoing_rule
    )
    model.incoming_routes = pyo.Constraint(
        model.cities, rule=incoming_rule
    )
    model.depot_position_constraint = pyo.Constraint(
        expr=model.position[0] == model.depot_position
    )

    def subtour_rule(problem, origin, destination):
        if origin == destination:
            return pyo.Constraint.Skip
        position_span = problem.position_upper - problem.position_lower
        return (
            problem.position[origin]
            - problem.position[destination]
            + (position_span + 1) * problem.route[origin, destination]
            <= position_span
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
        # APPsi raises this when it cannot load a feasible solution.
        # Other runtime errors are unexpected and must propagate.
        if "a feasible solution was not found" not in str(exc).lower():
            raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "no_solution"}

    return {"objective": obj_val, "status": "optimal"}