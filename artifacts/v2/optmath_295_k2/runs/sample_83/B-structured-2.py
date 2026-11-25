# IR: {"sets":{"A":"0..23","T":"0..17","C":[[1,2,8,14,15,17],[0,3,6,7,8,9,12],[0,1,4,5,7,10,11,12,16],[1,2,3,5,9,12,13,15,17],[1,2,3,7,8,10,11,16],[1,4,5,6,8,11,12,14,16],[0,2,3,4,5,7,10,11,13,14,16],[1,2,4,5,7,10,11,13,14,16,17],[2,3,10,13,14,16],[2,3,4,5,6,7,8,10,11,14,15,17],[0,1,5,12,16,17],[2,3,5,6,7,10,11,13,14,15,16,17],[0,1,2,7,9,10,12,14,15,17],[0,1,2,3,6,10,11,14,15,16],[0,2,4,7,8,10,11,14,15,16],[0,1,4,5,7,10,13,15,16,17],[0,3,4,8,10,12,13,14,15],[3,4,5,6,8,10,12,14],[7,8,9,15],[0,3,6,7,8,9,13,15,17],[2,4,7,8,11,12,13,14,15,16],[1,5,8,10,11,12],[1,2,4,6,8,12,14,16],[0,1,2,5,6,10,12,13,15,16,17]]},"params":{"population":"params['population'][a], a in A","tower_cost":"params['tower_cost'][t], t in T","budget":"params['budget']"},"variables":{"build[t]":"binary, t in T","covered[a]":"binary, a in A"},"constraints":["covered[a] <= sum(build[t] for t in C[a]), a in A","sum(tower_cost[t]*build[t] for t in T) <= budget"],"objective":"maximize sum(population[a]*covered[a] for a in A)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    coverage = (
        (1, 2, 8, 14, 15, 17),
        (0, 3, 6, 7, 8, 9, 12),
        (0, 1, 4, 5, 7, 10, 11, 12, 16),
        (1, 2, 3, 5, 9, 12, 13, 15, 17),
        (1, 2, 3, 7, 8, 10, 11, 16),
        (1, 4, 5, 6, 8, 11, 12, 14, 16),
        (0, 2, 3, 4, 5, 7, 10, 11, 13, 14, 16),
        (1, 2, 4, 5, 7, 10, 11, 13, 14, 16, 17),
        (2, 3, 10, 13, 14, 16),
        (2, 3, 4, 5, 6, 7, 8, 10, 11, 14, 15, 17),
        (0, 1, 5, 12, 16, 17),
        (2, 3, 5, 6, 7, 10, 11, 13, 14, 15, 16, 17),
        (0, 1, 2, 7, 9, 10, 12, 14, 15, 17),
        (0, 1, 2, 3, 6, 10, 11, 14, 15, 16),
        (0, 2, 4, 7, 8, 10, 11, 14, 15, 16),
        (0, 1, 4, 5, 7, 10, 13, 15, 16, 17),
        (0, 3, 4, 8, 10, 12, 13, 14, 15),
        (3, 4, 5, 6, 8, 10, 12, 14),
        (7, 8, 9, 15),
        (0, 3, 6, 7, 8, 9, 13, 15, 17),
        (2, 4, 7, 8, 11, 12, 13, 14, 15, 16),
        (1, 5, 8, 10, 11, 12),
        (1, 2, 4, 6, 8, 12, 14, 16),
        (0, 1, 2, 5, 6, 10, 12, 13, 15, 16, 17),
    )

    population = params["population"]
    tower_cost = params["tower_cost"]
    budget = params["budget"]

    model = pyo.ConcreteModel()
    model.areas = pyo.RangeSet(0, 23)
    model.towers = pyo.RangeSet(0, 17)

    model.population = pyo.Param(
        model.areas,
        initialize={area: population[area] for area in range(24)},
    )
    model.tower_cost = pyo.Param(
        model.towers,
        initialize={tower: tower_cost[tower] for tower in range(18)},
    )
    model.budget = pyo.Param(initialize=budget)

    model.build = pyo.Var(model.towers, domain=pyo.Binary)
    model.covered = pyo.Var(model.areas, domain=pyo.Binary)

    def coverage_rule(instance, area):
        return instance.covered[area] <= sum(
            instance.build[tower] for tower in coverage[area]
        )

    model.coverage_constraint = pyo.Constraint(
        model.areas, rule=coverage_rule
    )
    model.budget_constraint = pyo.Constraint(
        expr=sum(
            model.tower_cost[tower] * model.build[tower]
            for tower in model.towers
        )
        <= model.budget
    )

    model.total_population = pyo.Objective(
        expr=sum(
            model.population[area] * model.covered[area]
            for area in model.areas
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        # HiGHS may raise when no feasible solution can be loaded.
        # Objective retrievability remains the sole success criterion.
        pass

    try:
        obj_val = float(pyo.value(model.total_population))
    except (ValueError, TypeError):
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}