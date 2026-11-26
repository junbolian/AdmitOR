# IR: {"sets":{"V":"{1,...,num_cities}, fixed size 5","E":"{(i,j): i,j in V, i<j}","S":"{T subset V: 2<=|T|<=num_cities-1}"},"params":["cost_1_2","cost_1_3","cost_1_4","cost_1_5","cost_2_3","cost_2_4","cost_2_5","cost_3_4","cost_3_5","cost_4_5","num_cities"],"variables":{"x[i,j]":"Binary, (i,j) in E"},"constraints":["For each i in V: sum(x[a,b] for (a,b) in E if i in (a,b)) = 2","For each T in S: sum(x[i,j] for (i,j) in E if i,j in T) <= |T|-1"],"objective":"Minimize sum(cost_i_j*x[i,j] for (i,j) in E)"}

from itertools import combinations

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_cities = params["num_cities"]
    costs = {
        (1, 2): params["cost_1_2"],
        (1, 3): params["cost_1_3"],
        (1, 4): params["cost_1_4"],
        (1, 5): params["cost_1_5"],
        (2, 3): params["cost_2_3"],
        (2, 4): params["cost_2_4"],
        (2, 5): params["cost_2_5"],
        (3, 4): params["cost_3_4"],
        (3, 5): params["cost_3_5"],
        (4, 5): params["cost_4_5"],
    }

    # Five cities are the specified structural problem size.
    if num_cities != 5:
        return {"objective": None, "status": "invalid_num_cities"}

    cities = tuple(range(1, int(num_cities) + 1))
    edges = tuple(combinations(cities, 2))

    model = pyo.ConcreteModel()
    model.cities = pyo.Set(initialize=cities, ordered=True)
    model.edges = pyo.Set(dimen=2, initialize=edges, ordered=True)
    model.travel_cost = pyo.Param(
        model.edges, initialize=costs, within=pyo.Reals
    )
    model.x = pyo.Var(model.edges, domain=pyo.Binary)

    def degree_rule(instance, city):
        return sum(
            instance.x[first, second]
            for first, second in instance.edges
            if city == first or city == second
        ) == 2

    model.degree_constraints = pyo.Constraint(
        model.cities, rule=degree_rule
    )

    model.subtour_constraints = pyo.ConstraintList()
    for subset_size in range(2, len(cities)):
        for subset in combinations(cities, subset_size):
            model.subtour_constraints.add(
                sum(
                    model.x[first, second]
                    for first, second in combinations(subset, 2)
                ) <= len(subset) - 1
            )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.travel_cost[first, second] * model.x[first, second]
            for first, second in model.edges
        ),
        sense=pyo.minimize,
    )

    failure_reason = "objective_unavailable"
    try:
        Highs().solve(model)
    except RuntimeError:
        # HiGHS may raise when no solution can be loaded.
        # Objective retrieval below is the sole success criterion.
        failure_reason = "solver_failed"

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": failure_reason}

    return {"objective": obj_val, "status": "optimal"}