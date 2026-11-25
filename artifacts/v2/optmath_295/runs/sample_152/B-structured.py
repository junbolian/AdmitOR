# IR: {"sets":{"V":"range(n_cities)","A":"{(i,j) in V x V: i != j}","W":"V excluding 0"},"params":{"n_cities":"params['n_cities']","position_upper_bound":"params['position_upper_bound']","cost[i,j]":"params[f'cost_{i}_{j}'] for (i,j) in A"},"variables":{"x[i,j]":"Binary, (i,j) in A","u[i]":"Integer, 0 <= u[i] <= position_upper_bound, i in V"},"constraints":["sum(x[i,j] for j in V if j != i) = 1 for i in V","sum(x[i,j] for i in V if i != j) = 1 for j in V","u[0] = 0","u[i] >= 1 for i in W","u[i] - u[j] + n_cities*x[i,j] <= n_cities - 1 for distinct i,j in W"],"objective":"minimize sum(cost[i,j]*x[i,j] for (i,j) in A)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    n_cities = params["n_cities"]
    position_upper_bound = params["position_upper_bound"]

    cities = list(range(n_cities))
    arcs = [(i, j) for i in cities for j in cities if i != j]
    nondepot_cities = [i for i in cities if i != 0]

    model = pyo.ConcreteModel()

    model.cities = pyo.Set(initialize=cities, ordered=True)
    model.arcs = pyo.Set(dimen=2, initialize=arcs, ordered=True)
    model.nondepot_cities = pyo.Set(
        initialize=nondepot_cities, ordered=True
    )

    model.city_count = pyo.Param(initialize=n_cities)
    model.position_limit = pyo.Param(initialize=position_upper_bound)
    model.travel_cost = pyo.Param(
        model.arcs,
        initialize={
            (i, j): params[f"cost_{i}_{j}"]
            for i, j in arcs
        },
        within=pyo.Reals,
    )

    model.x = pyo.Var(model.arcs, domain=pyo.Binary)
    model.u = pyo.Var(
        model.cities,
        domain=pyo.NonNegativeIntegers,
        bounds=(0, model.position_limit),
    )

    def departure_rule(instance, i):
        return sum(
            instance.x[i, j] for j in instance.cities if j != i
        ) == 1

    model.departure_constraints = pyo.Constraint(
        model.cities, rule=departure_rule
    )

    def arrival_rule(instance, j):
        return sum(
            instance.x[i, j] for i in instance.cities if i != j
        ) == 1

    model.arrival_constraints = pyo.Constraint(
        model.cities, rule=arrival_rule
    )

    model.depot_position = pyo.Constraint(expr=model.u[0] == 0)

    def positive_position_rule(instance, i):
        return instance.u[i] >= 1

    model.positive_position_constraints = pyo.Constraint(
        model.nondepot_cities, rule=positive_position_rule
    )

    def subtour_rule(instance, i, j):
        if i == j:
            return pyo.Constraint.Skip
        return (
            instance.u[i]
            - instance.u[j]
            + instance.city_count * instance.x[i, j]
            <= instance.city_count - 1
        )

    model.subtour_constraints = pyo.Constraint(
        model.nondepot_cities,
        model.nondepot_cities,
        rule=subtour_rule,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.travel_cost[i, j] * model.x[i, j]
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