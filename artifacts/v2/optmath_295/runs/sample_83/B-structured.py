# IR: {"sets":{"areas":"0..23","towers":"0..17","coverage":"fixed area-to-tower adjacency below"},"params":{"populations":"params['populations'][area]","tower_costs":"params['tower_costs'][tower]","budget":"params['budget']"},"variables":{"build[tower]":"binary","covered[area]":"binary"},"constraints":["covered[area] <= sum(build[tower] for tower in coverage[area]), for each area","sum(tower_costs[tower] * build[tower] for tower in towers) <= budget"],"objective":"maximize sum(populations[area] * covered[area] for area in areas)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    populations = params["populations"]
    tower_costs = params["tower_costs"]
    budget = params["budget"]

    coverage = {
        0: (1, 2, 8, 14, 15, 17),
        1: (0, 3, 6, 7, 8, 9, 12),
        2: (0, 1, 4, 5, 7, 10, 11, 12, 16),
        3: (1, 2, 3, 5, 9, 12, 13, 15, 17),
        4: (1, 2, 3, 7, 8, 10, 11, 16),
        5: (1, 4, 5, 6, 8, 11, 12, 14, 16),
        6: (0, 2, 3, 4, 5, 7, 10, 11, 13, 14, 16),
        7: (1, 2, 4, 5, 7, 10, 11, 13, 14, 16, 17),
        8: (2, 3, 10, 13, 14, 16),
        9: (2, 3, 4, 5, 6, 7, 8, 10, 11, 14, 15, 17),
        10: (0, 1, 5, 12, 16, 17),
        11: (2, 3, 5, 6, 7, 10, 11, 13, 14, 15, 16, 17),
        12: (0, 1, 2, 7, 9, 10, 12, 14, 15, 17),
        13: (0, 1, 2, 3, 6, 10, 11, 14, 15, 16),
        14: (0, 2, 4, 7, 8, 10, 11, 14, 15, 16),
        15: (0, 1, 4, 5, 7, 10, 13, 15, 16, 17),
        16: (0, 3, 4, 8, 10, 12, 13, 14, 15),
        17: (3, 4, 5, 6, 8, 10, 12, 14),
        18: (7, 8, 9, 15),
        19: (0, 3, 6, 7, 8, 9, 13, 15, 17),
        20: (2, 4, 7, 8, 11, 12, 13, 14, 15, 16),
        21: (1, 5, 8, 10, 11, 12),
        22: (1, 2, 4, 6, 8, 12, 14, 16),
        23: (0, 1, 2, 5, 6, 10, 12, 13, 15, 16, 17),
    }

    model = pyo.ConcreteModel()
    model.areas = pyo.RangeSet(0, 23)
    model.towers = pyo.RangeSet(0, 17)

    model.population = pyo.Param(
        model.areas,
        initialize={area: populations[area] for area in model.areas},
    )
    model.tower_cost = pyo.Param(
        model.towers,
        initialize={tower: tower_costs[tower] for tower in model.towers},
    )
    model.budget_limit = pyo.Param(initialize=budget)

    model.build = pyo.Var(model.towers, domain=pyo.Binary)
    model.covered = pyo.Var(model.areas, domain=pyo.Binary)

    def coverage_rule(instance, area):
        return instance.covered[area] <= sum(
            instance.build[tower] for tower in coverage[area]
        )

    model.coverage_constraints = pyo.Constraint(
        model.areas, rule=coverage_rule
    )
    model.budget_constraint = pyo.Constraint(
        expr=sum(
            model.tower_cost[tower] * model.build[tower]
            for tower in model.towers
        )
        <= model.budget_limit
    )

    model.total_covered_population = pyo.Objective(
        expr=sum(
            model.population[area] * model.covered[area]
            for area in model.areas
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_covered_population))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}