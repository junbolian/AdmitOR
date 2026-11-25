# IR: {"sets":{"A":"0..21","T":"0..19","C[a]":"fixed tower adjacency in coverage[a]"},"params":{"population":"params['population'][a], a in A","tower_cost":"params['tower_cost'][t], t in T","budget":"params['budget']"},"variables":{"build[t]":"Binary, t in T","covered[a]":"Binary, a in A"},"constraints":["sum(tower_cost[t]*build[t] for t in T) <= budget","covered[a] <= sum(build[t] for t in C[a]), for each a in A","covered[a] >= build[t], for each a in A and t in C[a]"],"objective":"maximize sum(population[a]*covered[a] for a in A)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    coverage = {
        0: (0, 1, 4, 5, 6, 7, 11, 12, 14, 16, 18),
        1: (0, 1, 4, 6, 7, 13, 14, 17),
        2: (6, 7, 8, 11, 12, 14, 15, 16, 18),
        3: (1, 2, 4, 5, 8, 9, 12, 13, 14, 17, 18, 19),
        4: (0, 3, 9, 10, 11, 13, 14, 17, 18, 19),
        5: (0, 1, 5, 8, 9, 11, 12, 13, 16, 17, 19),
        6: (0, 2, 3, 4, 6, 7, 9, 14, 17, 19),
        7: (0, 4, 5, 6, 10, 11, 14, 15, 18),
        8: (0, 1, 7, 8, 9, 10, 11, 12, 16, 17, 18, 19),
        9: (5, 10, 15),
        10: (0, 5, 7, 8, 9, 11, 13, 15, 16, 17, 19),
        11: (0, 1, 3, 6, 7, 8, 10, 12, 16, 17, 19),
        12: (1, 4, 8, 11, 12, 13, 14, 15, 16, 17, 18, 19),
        13: (0, 2, 4, 5, 6, 7, 9, 13, 14, 15, 16, 19),
        14: (4, 5, 6, 8, 11, 14, 15),
        15: (0, 1, 2, 8, 10, 11, 17, 19),
        16: (0, 2, 3, 4, 8, 10, 11, 13, 14, 15, 16, 18),
        17: (0, 2, 3, 4, 5, 6, 7, 8, 11, 14, 17, 18, 19),
        18: (2, 5, 8, 11, 13, 15, 16, 18),
        19: (3, 5, 6, 7, 8, 10, 11, 12, 15, 16, 18, 19),
        20: (0, 4, 8, 9, 11, 14, 16, 18, 19),
        21: (0, 4, 5, 6, 7, 9, 10, 15, 17, 18, 19),
    }

    population = params["population"]
    tower_cost = params["tower_cost"]
    budget = params["budget"]

    model = pyo.ConcreteModel()
    model.areas = pyo.RangeSet(0, 21)
    model.towers = pyo.RangeSet(0, 19)
    model.coverage_pairs = pyo.Set(
        dimen=2,
        initialize=[
            (area, tower)
            for area in model.areas
            for tower in coverage[area]
        ],
    )

    model.population = pyo.Param(
        model.areas,
        initialize={area: population[area] for area in model.areas},
        within=pyo.NonNegativeReals,
    )
    model.tower_cost = pyo.Param(
        model.towers,
        initialize={tower: tower_cost[tower] for tower in model.towers},
        within=pyo.NonNegativeReals,
    )
    model.budget = pyo.Param(initialize=budget, within=pyo.Reals)

    model.build = pyo.Var(model.towers, domain=pyo.Binary)
    model.covered = pyo.Var(model.areas, domain=pyo.Binary)

    model.budget_limit = pyo.Constraint(
        expr=sum(
            model.tower_cost[tower] * model.build[tower]
            for tower in model.towers
        ) <= model.budget
    )

    def coverage_upper_rule(model, area):
        return model.covered[area] <= sum(
            model.build[tower] for tower in coverage[area]
        )

    model.coverage_upper = pyo.Constraint(
        model.areas, rule=coverage_upper_rule
    )

    def coverage_lower_rule(model, area, tower):
        return model.covered[area] >= model.build[tower]

    model.coverage_lower = pyo.Constraint(
        model.coverage_pairs, rule=coverage_lower_rule
    )

    model.total_population = pyo.Objective(
        expr=sum(
            model.population[area] * model.covered[area]
            for area in model.areas
        ),
        sense=pyo.maximize,
    )

    failure_reason = "no_solution"
    try:
        Highs().solve(model)
    except RuntimeError:
        # HiGHS can raise when no feasible solution is available to load.
        failure_reason = "solve_failed"

    try:
        obj_val = float(pyo.value(model.total_population))
    except (ValueError, TypeError):
        return {"objective": None, "status": failure_reason}

    return {"objective": obj_val, "status": "optimal"}