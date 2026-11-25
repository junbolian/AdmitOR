# IR: {"sets":{"V":"range(num_cities)","A":"{(i,j) in V x V: i != j}","S":"V excluding city 0"},"params":{"num_cities":"params['num_cities']","u_lower":"params['u_lower']","u_upper":"params['u_upper']","cost[i,j]":"params[f'travel_cost_{i}_{j}'] for (i,j) in A"},"variables":{"x[i,j]":"binary for (i,j) in A","u[i]":"continuous in [u_lower,u_upper] for i in V"},"constraints":["sum(x[i,j] for j in V if j != i) = 1 for i in V","sum(x[i,j] for i in V if i != j) = 1 for j in V","u[i] - u[j] + num_cities*x[i,j] <= num_cities - 1 for distinct i,j in S"],"objective":"minimize sum(cost[i,j]*x[i,j] for (i,j) in A)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_cities = int(params["num_cities"])
    u_lower = params["u_lower"]
    u_upper = params["u_upper"]

    cities = range(num_cities)
    arcs = [(i, j) for i in cities for j in cities if i != j]
    costs = {
        (i, j): params[f"travel_cost_{i}_{j}"]
        for i, j in arcs
    }

    model = pyo.ConcreteModel()
    model.V = pyo.Set(initialize=cities, ordered=True)
    model.A = pyo.Set(initialize=arcs, dimen=2, ordered=True)
    model.S = pyo.Set(
        initialize=[i for i in cities if i != 0],
        ordered=True,
    )

    model.city_count = pyo.Param(
        initialize=num_cities,
        within=pyo.PositiveIntegers,
    )
    model.order_lower = pyo.Param(initialize=u_lower, within=pyo.Reals)
    model.order_upper = pyo.Param(initialize=u_upper, within=pyo.Reals)
    model.travel_cost = pyo.Param(
        model.A,
        initialize=costs,
        within=pyo.Reals,
    )

    model.x = pyo.Var(model.A, domain=pyo.Binary)
    model.u = pyo.Var(
        model.V,
        domain=pyo.Reals,
        bounds=(model.order_lower, model.order_upper),
    )

    def departure_rule(model, i):
        return sum(model.x[i, j] for j in model.V if j != i) == 1

    model.departure_once = pyo.Constraint(model.V, rule=departure_rule)

    def arrival_rule(model, j):
        return sum(model.x[i, j] for i in model.V if i != j) == 1

    model.arrival_once = pyo.Constraint(model.V, rule=arrival_rule)

    def subtour_rule(model, i, j):
        if i == j:
            return pyo.Constraint.Skip
        return (
            model.u[i] - model.u[j] + model.city_count * model.x[i, j]
            <= model.city_count - 1
        )

    model.subtour_elimination = pyo.Constraint(
        model.S,
        model.S,
        rule=subtour_rule,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.travel_cost[i, j] * model.x[i, j]
            for i, j in model.A
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}