# {
#   "sets": {"V": "range(n_cities)", "W": "V excluding 0", "A": "all (i,j) in V x V with i != j"},
#   "params": {"n_cities": "params['n_cities']", "max_position": "params['max_position']", "c[i,j]": "params[f'c_{i}_{j}'] for every (i,j) in A"},
#   "variables": {"x[i,j]": "Binary for (i,j) in A", "u[i]": "Real in [0,max_position] for i in V"},
#   "constraints": [
#     "sum(x[i,j] for j in V if j != i) == 1 for every i in V",
#     "sum(x[i,j] for i in V if i != j) == 1 for every j in V",
#     "u[0] == 0",
#     "u[i] - u[j] + n_cities*x[i,j] <= n_cities - 1 for distinct i,j in W"
#   ],
#   "objective": "minimize sum(c[i,j]*x[i,j] for (i,j) in A)"
# }

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    n_cities = int(params["n_cities"])
    max_position = params["max_position"]

    cities = list(range(n_cities))
    other_cities = [city for city in cities if city != 0]
    arcs = [
        (origin, destination)
        for origin in cities
        for destination in cities
        if origin != destination
    ]
    costs = {
        (origin, destination): params[f"c_{origin}_{destination}"]
        for origin, destination in arcs
    }

    model = pyo.ConcreteModel()

    model.V = pyo.Set(initialize=cities, ordered=True)
    model.W = pyo.Set(initialize=other_cities, ordered=True)
    model.A = pyo.Set(dimen=2, initialize=arcs, ordered=True)

    model.city_count = pyo.Param(
        initialize=n_cities, within=pyo.PositiveIntegers
    )
    model.position_limit = pyo.Param(
        initialize=max_position, within=pyo.NonNegativeReals
    )
    model.travel_cost = pyo.Param(
        model.A, initialize=costs, within=pyo.Reals
    )

    model.x = pyo.Var(model.A, domain=pyo.Binary)
    model.u = pyo.Var(
        model.V,
        domain=pyo.Reals,
        bounds=(0, model.position_limit),
    )

    def departure_rule(route_model, origin):
        return sum(
            route_model.x[origin, destination]
            for destination in route_model.V
            if destination != origin
        ) == 1

    model.departure_constraints = pyo.Constraint(
        model.V, rule=departure_rule
    )

    def arrival_rule(route_model, destination):
        return sum(
            route_model.x[origin, destination]
            for origin in route_model.V
            if origin != destination
        ) == 1

    model.arrival_constraints = pyo.Constraint(
        model.V, rule=arrival_rule
    )

    model.start_position_constraint = pyo.Constraint(
        expr=model.u[0] == 0
    )

    def subtour_rule(route_model, origin, destination):
        if origin == destination:
            return pyo.Constraint.Skip
        return (
            route_model.u[origin]
            - route_model.u[destination]
            + route_model.city_count * route_model.x[origin, destination]
            <= route_model.city_count - 1
        )

    model.subtour_constraints = pyo.Constraint(
        model.W, model.W, rule=subtour_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.travel_cost[origin, destination]
            * model.x[origin, destination]
            for origin, destination in model.A
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPsi raises this specific error when no solution can be loaded.
        # Unexpected solver errors propagate.
        if "a feasible solution was not found" not in str(exc).lower():
            raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}