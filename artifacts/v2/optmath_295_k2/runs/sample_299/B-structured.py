# IR: {"sets":{"regions":"0..10","towers":"0..8","serves":{"0":[4,5,6,8],"1":[1,2,3,4,5,7],"2":[3,5,7],"3":[1,3,4,5,6],"4":[0,3,4,7],"5":[5,7,8],"6":[1,3,6,8],"7":[6,7],"8":[3],"9":[0,2,3,4,5,8],"10":[1,2,4,6,7,8]}},"params":{"population":"population[r] from params","tower_cost":"tower_cost[t] from params","budget":"budget from params"},"variables":{"build[t]":"binary","covered[r]":"binary"},"constraints":["covered[r] <= sum(build[t] for t in serves[r]), for each region r","covered[r] >= build[t], for each region r and t in serves[r]","sum(tower_cost[t]*build[t] for t in towers) <= budget"],"objective":"maximize sum(population[r]*covered[r] for r in regions)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    population = params["population"]
    tower_cost = params["tower_cost"]
    budget = params["budget"]

    serves = {
        0: (4, 5, 6, 8),
        1: (1, 2, 3, 4, 5, 7),
        2: (3, 5, 7),
        3: (1, 3, 4, 5, 6),
        4: (0, 3, 4, 7),
        5: (5, 7, 8),
        6: (1, 3, 6, 8),
        7: (6, 7),
        8: (3,),
        9: (0, 2, 3, 4, 5, 8),
        10: (1, 2, 4, 6, 7, 8),
    }

    model = pyo.ConcreteModel()
    model.regions = pyo.RangeSet(0, 10)
    model.towers = pyo.RangeSet(0, 8)
    model.coverage_pairs = pyo.Set(
        dimen=2,
        initialize=[
            (region, tower)
            for region in range(11)
            for tower in serves[region]
        ],
    )

    model.population = pyo.Param(
        model.regions,
        initialize={region: population[region] for region in range(11)},
    )
    model.tower_cost = pyo.Param(
        model.towers,
        initialize={tower: tower_cost[tower] for tower in range(9)},
    )
    model.budget = pyo.Param(initialize=budget)

    model.build = pyo.Var(model.towers, domain=pyo.Binary)
    model.covered = pyo.Var(model.regions, domain=pyo.Binary)

    def coverage_upper_rule(instance, region):
        return instance.covered[region] <= sum(
            instance.build[tower] for tower in serves[region]
        )

    model.coverage_upper = pyo.Constraint(
        model.regions, rule=coverage_upper_rule
    )

    def coverage_lower_rule(instance, region, tower):
        return instance.covered[region] >= instance.build[tower]

    model.coverage_lower = pyo.Constraint(
        model.coverage_pairs, rule=coverage_lower_rule
    )

    model.budget_limit = pyo.Constraint(
        expr=sum(
            model.tower_cost[tower] * model.build[tower]
            for tower in model.towers
        ) <= model.budget
    )

    model.total_coverage = pyo.Objective(
        expr=sum(
            model.population[region] * model.covered[region]
            for region in model.regions
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_coverage))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}