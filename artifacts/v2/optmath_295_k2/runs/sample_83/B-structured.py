# IR: {"sets":{"areas":"0..23","towers":"0..17","covering_towers":"fixed adjacency mapping defined below"},"params":{"population":"params['population'][area]","tower_cost":"params['tower_cost'][tower]","budget":"params['budget']"},"variables":{"build[tower]":"binary","covered[area]":"binary"},"constraints":["covered[area] <= sum(build[tower] for tower in covering_towers[area]), for every area","sum(tower_cost[tower] * build[tower] for tower in towers) <= budget"],"objective":"maximize sum(population[area] * covered[area] for area in areas)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    covering_towers = {
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
    model.covering_towers = pyo.Set(
        model.areas,
        within=model.towers,
        initialize=covering_towers,
    )

    model.population = pyo.Param(
        model.areas,
        initialize=lambda model, area: params["population"][area],
        within=pyo.Reals,
    )
    model.tower_cost = pyo.Param(
        model.towers,
        initialize=lambda model, tower: params["tower_cost"][tower],
        within=pyo.Reals,
    )
    model.budget = pyo.Param(
        initialize=params["budget"],
        within=pyo.Reals,
    )

    model.build = pyo.Var(model.towers, domain=pyo.Binary)
    model.covered = pyo.Var(model.areas, domain=pyo.Binary)

    def coverage_rule(model, area):
        return model.covered[area] <= sum(
            model.build[tower]
            for tower in model.covering_towers[area]
        )

    model.coverage_constraint = pyo.Constraint(
        model.areas,
        rule=coverage_rule,
    )
    model.budget_constraint = pyo.Constraint(
        expr=sum(
            model.tower_cost[tower] * model.build[tower]
            for tower in model.towers
        ) <= model.budget
    )
    model.total_population = pyo.Objective(
        expr=sum(
            model.population[area] * model.covered[area]
            for area in model.areas
        ),
        sense=pyo.maximize,
    )

    solver_failed = False
    try:
        Highs().solve(model)
    except RuntimeError:
        # HiGHS can raise when no feasible solution can be loaded.
        solver_failed = True

    try:
        obj_val = float(pyo.value(model.total_population))
    except (ValueError, TypeError):
        return {
            "objective": None,
            "status": (
                "infeasible_or_failed"
                if solver_failed
                else "objective_unavailable"
            ),
        }

    return {"objective": obj_val, "status": "optimal"}