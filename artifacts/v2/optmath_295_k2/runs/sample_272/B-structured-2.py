# IR: {"sets":{"areas":[0,1,2,3,4,5,6,7,8],"towers":[0,1,2,3,4,5,6,7,8],"serving":{"0":[2,4,5,6,7],"1":[0,1,6,8],"2":[1,6,8],"3":[1,2,6,7],"4":[0,2,3,6,7,8],"5":[0,1,2,6,7],"6":[0,1,2,4],"7":[1,2,4,5,6],"8":[0,1,3,4,5,8]}},"params":{"population":"params['population'][area]","tower_cost":"params['tower_cost'][tower]","budget":"params['budget']"},"variables":{"build[tower]":"binary","covered[area]":"binary"},"constraints":["covered[area] <= sum(build[tower] for tower in serving[area]), for each area","sum(tower_cost[tower]*build[tower] for tower in towers) <= budget"],"objective":"maximize sum(population[area]*covered[area] for area in areas)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    population = params["population"]
    tower_cost = params["tower_cost"]
    budget = params["budget"]

    serving = {
        0: (2, 4, 5, 6, 7),
        1: (0, 1, 6, 8),
        2: (1, 6, 8),
        3: (1, 2, 6, 7),
        4: (0, 2, 3, 6, 7, 8),
        5: (0, 1, 2, 6, 7),
        6: (0, 1, 2, 4),
        7: (1, 2, 4, 5, 6),
        8: (0, 1, 3, 4, 5, 8),
    }

    model = pyo.ConcreteModel()
    model.areas = pyo.RangeSet(0, 8)
    model.towers = pyo.RangeSet(0, 8)

    model.population = pyo.Param(
        model.areas,
        initialize={area: population[area] for area in model.areas},
    )
    model.tower_cost = pyo.Param(
        model.towers,
        initialize={tower: tower_cost[tower] for tower in model.towers},
    )
    model.budget = pyo.Param(initialize=budget)

    model.build = pyo.Var(model.towers, domain=pyo.Binary)
    model.covered = pyo.Var(model.areas, domain=pyo.Binary)

    def coverage_rule(instance, area):
        return instance.covered[area] <= sum(
            instance.build[tower] for tower in serving[area]
        )

    model.coverage_constraint = pyo.Constraint(
        model.areas, rule=coverage_rule
    )
    model.budget_constraint = pyo.Constraint(
        expr=sum(
            model.tower_cost[tower] * model.build[tower]
            for tower in model.towers
        ) <= model.budget
    )
    model.total_coverage = pyo.Objective(
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
        obj_val = float(pyo.value(model.total_coverage))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}