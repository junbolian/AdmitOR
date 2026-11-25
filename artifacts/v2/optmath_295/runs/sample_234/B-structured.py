# IR: {"sets":{"A":"0..24","T":"0..17","C[a]":"designated covering towers in coverage below"},"params":{"population[a]":"params['population'][a]","tower_cost[t]":"params['tower_cost'][t]","budget":"params['budget']"},"variables":{"build[t]":"Binary","covered[a]":"Binary"},"constraints":["sum(tower_cost[t]*build[t] for t in T) <= budget","covered[a] <= sum(build[t] for t in C[a]) for each a in A"],"objective":"maximize sum(population[a]*covered[a] for a in A)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    population = params["population"]
    tower_cost = params["tower_cost"]
    budget = params["budget"]

    coverage = {
        0: (1, 4, 7, 8, 9, 13, 15, 16),
        1: (7, 9, 11, 12, 13, 14, 15, 16),
        2: (1, 2, 4, 5, 7, 9, 10, 11, 14, 17),
        3: (1, 3, 4, 7, 8, 13, 14, 17),
        4: (5, 6, 7, 9, 10, 13, 16, 17),
        5: (0, 1, 3, 4, 9, 10, 12, 14, 17),
        6: (0, 3, 4, 5, 6, 9, 10, 12, 14, 15, 16, 17),
        7: (3, 4, 5, 6, 7, 8, 11, 13, 14),
        8: (0, 3, 4, 5, 6, 7, 8, 10, 11, 14, 15),
        9: (1, 2, 3, 4, 7, 8, 10, 11, 12, 15, 16, 17),
        10: (2, 8, 10, 15, 16),
        11: (0, 2, 3, 5, 12, 13, 14, 15, 17),
        12: (2, 4, 5, 7, 8, 10, 12, 14, 17),
        13: (2, 5, 7, 8, 9, 15, 16),
        14: (1, 2, 3, 5, 6, 7, 8, 9, 10, 11, 15),
        15: (0, 1, 3, 4, 6, 7, 8, 9, 10, 13, 15, 16, 17),
        16: (0, 2, 3, 4, 9, 10, 12, 13, 14, 17),
        17: (0, 2, 3, 4, 5, 6, 10, 11, 12, 13, 14, 15),
        18: (2, 4, 5, 7, 9, 10, 11, 12, 16, 17),
        19: (0, 2, 5, 6, 8, 9, 12, 13, 15, 16, 17),
        20: (1, 2, 4, 5, 8, 10, 13, 14, 16),
        21: (0, 1, 3, 4, 7, 10, 12, 14, 17),
        22: (4, 5, 7, 9, 11, 14, 15, 16),
        23: (4, 11, 14, 16),
        24: (9, 11, 17),
    }

    model = pyo.ConcreteModel()
    model.areas = pyo.RangeSet(0, 24)
    model.towers = pyo.RangeSet(0, 17)
    model.covering_towers = pyo.Set(
        model.areas,
        within=model.towers,
        initialize=coverage,
    )

    model.area_population = pyo.Param(
        model.areas,
        initialize={a: population[a] for a in model.areas},
    )
    model.construction_cost = pyo.Param(
        model.towers,
        initialize={t: tower_cost[t] for t in model.towers},
    )
    model.cost_limit = pyo.Param(initialize=budget)

    model.build = pyo.Var(model.towers, domain=pyo.Binary)
    model.covered = pyo.Var(model.areas, domain=pyo.Binary)

    model.budget_constraint = pyo.Constraint(
        expr=sum(
            model.construction_cost[t] * model.build[t]
            for t in model.towers
        ) <= model.cost_limit
    )

    def coverage_rule(instance, a):
        return instance.covered[a] <= sum(
            instance.build[t] for t in instance.covering_towers[a]
        )

    model.coverage_constraint = pyo.Constraint(
        model.areas,
        rule=coverage_rule,
    )

    model.total_population = pyo.Objective(
        expr=sum(
            model.area_population[a] * model.covered[a]
            for a in model.areas
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_population))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}