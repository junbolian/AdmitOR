# IR: {"sets":{"regions":"0..9","towers":"0..6","covering_towers":{"0":[0,3,5,6],"1":[2,3,4,6],"2":[0,1,4,5,6],"3":[0,3,4],"4":[0,3,4],"5":[1,2,3],"6":[1,2,3,4],"7":[1,2,3,4,5,6],"8":[0,1,2,4,5],"9":[1,4,6]}},"params":{"population":"params['population'][region]","tower_cost":"params['tower_cost'][tower]","budget":"params['budget']"},"variables":{"build[tower]":"binary","covered[region]":"binary"},"constraints":["covered[region] <= sum(build[tower] for tower in covering_towers[region]) for each region","sum(tower_cost[tower] * build[tower] for each tower) <= budget"],"objective":"maximize sum(population[region] * covered[region] for each region)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    covering_towers = {
        0: (0, 3, 5, 6),
        1: (2, 3, 4, 6),
        2: (0, 1, 4, 5, 6),
        3: (0, 3, 4),
        4: (0, 3, 4),
        5: (1, 2, 3),
        6: (1, 2, 3, 4),
        7: (1, 2, 3, 4, 5, 6),
        8: (0, 1, 2, 4, 5),
        9: (1, 4, 6),
    }

    model = pyo.ConcreteModel()
    model.regions = pyo.RangeSet(0, 9)
    model.towers = pyo.RangeSet(0, 6)

    model.population = pyo.Param(
        model.regions,
        initialize={
            region: params["population"][region]
            for region in model.regions
        },
    )
    model.tower_cost = pyo.Param(
        model.towers,
        initialize={
            tower: params["tower_cost"][tower]
            for tower in model.towers
        },
    )
    model.budget = pyo.Param(initialize=params["budget"])

    model.build = pyo.Var(model.towers, domain=pyo.Binary)
    model.covered = pyo.Var(model.regions, domain=pyo.Binary)

    def coverage_rule(instance, region):
        return instance.covered[region] <= sum(
            instance.build[tower]
            for tower in covering_towers[region]
        )

    model.coverage_constraint = pyo.Constraint(
        model.regions, rule=coverage_rule
    )
    model.budget_constraint = pyo.Constraint(
        expr=sum(
            model.tower_cost[tower] * model.build[tower]
            for tower in model.towers
        ) <= model.budget
    )
    model.total_population = pyo.Objective(
        expr=sum(
            model.population[region] * model.covered[region]
            for region in model.regions
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_population))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}