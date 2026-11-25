# IR: {
#   "sets": {"V": "range(num_cities)", "A": "[(i,j) for i in V for j in V if i != j]", "W": "V excluding city 0"},
#   "params": {"num_cities": "params['num_cities']", "cost[i,j]": "params[f'cost_{i}_{j}'] for (i,j) in A", "position_lower": "params['position_lower']", "position_upper": "params['position_upper']"},
#   "variables": {"x[i,j]": "binary for (i,j) in A", "u[i]": "continuous in [position_lower, position_upper] for i in V"},
#   "constraints": ["sum(x[i,j] for j in V if j != i) == 1 for i in V", "sum(x[i,j] for i in V if i != j) == 1 for j in V", "u[0] == 0", "u[i] - u[j] + num_cities*x[i,j] <= num_cities - 1 for distinct i,j in W"],
#   "objective": "minimize sum(cost[i,j]*x[i,j] for (i,j) in A)"
# }

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.city_count = pyo.Param(
        initialize=params["num_cities"],
        within=pyo.PositiveIntegers,
    )
    model.position_minimum = pyo.Param(
        initialize=params["position_lower"],
        within=pyo.Reals,
    )
    model.position_maximum = pyo.Param(
        initialize=params["position_upper"],
        within=pyo.Reals,
    )

    model.cities = pyo.Set(
        initialize=range(params["num_cities"]),
        ordered=True,
    )
    model.other_cities = pyo.Set(
        initialize=[city for city in model.cities if city != 0],
        ordered=True,
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
        model.arcs,
        initialize={
            (origin, destination): params[f"cost_{origin}_{destination}"]
            for origin, destination in model.arcs
        },
        within=pyo.Reals,
    )

    model.x = pyo.Var(model.arcs, domain=pyo.Binary)
    model.u = pyo.Var(
        model.cities,
        domain=pyo.Reals,
        bounds=(model.position_minimum, model.position_maximum),
    )

    def departure_rule(problem, origin):
        return sum(
            problem.x[origin, destination]
            for destination in problem.cities
            if destination != origin
        ) == 1

    def arrival_rule(problem, destination):
        return sum(
            problem.x[origin, destination]
            for origin in problem.cities
            if origin != destination
        ) == 1

    def subtour_rule(problem, origin, destination):
        if origin == destination:
            return pyo.Constraint.Skip
        return (
            problem.u[origin]
            - problem.u[destination]
            + problem.city_count * problem.x[origin, destination]
            <= problem.city_count - 1
        )

    model.departure_constraints = pyo.Constraint(
        model.cities, rule=departure_rule
    )
    model.arrival_constraints = pyo.Constraint(
        model.cities, rule=arrival_rule
    )
    model.depot_position = pyo.Constraint(expr=model.u[0] == 0)
    model.subtour_constraints = pyo.Constraint(
        model.other_cities,
        model.other_cities,
        rule=subtour_rule,
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
    except RuntimeError as exc:
        if "a feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}