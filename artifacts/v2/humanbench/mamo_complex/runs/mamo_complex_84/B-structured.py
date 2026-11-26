# IR: {"sets":{"V":"{1,...,n_cities}, with n_cities frozen at 6","E":"{(i,j): i,j in V, i<j}","S":"{U subset V: 2<=|U|<n_cities}"},"params":["cost_12","cost_13","cost_14","cost_15","cost_16","cost_23","cost_24","cost_25","cost_26","cost_34","cost_35","cost_36","cost_45","cost_46","cost_56","n_cities"],"derived":{"c[i,j]":"params['cost_'+str(i)+str(j)] for (i,j) in E"},"variables":{"x[i,j]":"Binary for (i,j) in E"},"constraints":["sum(x[i,j] for (i,j) in E if v in (i,j)) = 2 for every v in V","sum(x[i,j] for (i,j) in E if i in U and j in U) <= |U|-1 for every U in S"],"objective":"minimize sum(c[i,j]*x[i,j] for (i,j) in E)"}

from itertools import combinations

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    n_cities = params["n_cities"]
    if n_cities != 6:
        raise ValueError("n_cities must equal the frozen index-set size of 6.")
    n_cities = int(n_cities)

    cities = tuple(range(1, n_cities + 1))
    edges = tuple(combinations(cities, 2))
    edge_costs = {
        (city_i, city_j): params[f"cost_{city_i}{city_j}"]
        for city_i, city_j in edges
    }

    model = pyo.ConcreteModel()
    model.cities = pyo.Set(initialize=cities, ordered=True)
    model.edges = pyo.Set(dimen=2, initialize=edges, ordered=True)
    model.travel_cost = pyo.Param(
        model.edges,
        initialize=edge_costs,
        within=pyo.Reals,
    )
    model.x = pyo.Var(model.edges, domain=pyo.Binary)

    def degree_rule(model, city):
        return sum(
            model.x[city_i, city_j]
            for city_i, city_j in model.edges
            if city == city_i or city == city_j
        ) == 2

    model.degree_constraints = pyo.Constraint(
        model.cities, rule=degree_rule
    )

    model.subtour_constraints = pyo.ConstraintList()
    for subset_size in range(2, n_cities):
        for subset in combinations(cities, subset_size):
            model.subtour_constraints.add(
                sum(
                    model.x[city_i, city_j]
                    for city_i, city_j in combinations(subset, 2)
                )
                <= subset_size - 1
            )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.travel_cost[city_i, city_j] * model.x[city_i, city_j]
            for city_i, city_j in model.edges
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "A feasible solution was not found" not in str(exc):
            raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "no_solution"}

    return {"objective": obj_val, "status": "optimal"}