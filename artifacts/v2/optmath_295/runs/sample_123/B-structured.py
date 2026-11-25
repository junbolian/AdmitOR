# IR: {"sets":{"regions":"0..9","towers":"0..6"},"params":{"populations":"params['populations'][region]","tower_costs":"params['tower_costs'][tower]","budget":"params['budget']","coverage":{"0":[0,3,5,6],"1":[2,3,4,6],"2":[0,1,4,5,6],"3":[0,3,4],"4":[0,3,4],"5":[1,2,3],"6":[1,2,3,4],"7":[1,2,3,4,5,6],"8":[0,1,2,4,5],"9":[1,4,6]}},"variables":{"build[tower]":"Binary","covered[region]":"Binary"},"constraints":["For each region: covered[region] <= sum(build[tower] for tower in coverage[region])","sum(tower_costs[tower] * build[tower] for tower in towers) <= budget"],"objective":"maximize sum(populations[region] * covered[region] for region in regions)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    coverage = {
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

    model.populations = pyo.Param(
        model.regions,
        initialize={
            region: params["populations"][region]
            for region in range(10)
        },
    )
    model.tower_costs = pyo.Param(
        model.towers,
        initialize={
            tower: params["tower_costs"][tower]
            for tower in range(7)
        },
    )
    model.budget = pyo.Param(initialize=params["budget"])

    model.build = pyo.Var(model.towers, domain=pyo.Binary)
    model.covered = pyo.Var(model.regions, domain=pyo.Binary)

    def coverage_rule(instance, region):
        return instance.covered[region] <= sum(
            instance.build[tower] for tower in coverage[region]
        )

    model.coverage_constraints = pyo.Constraint(
        model.regions, rule=coverage_rule
    )
    model.budget_constraint = pyo.Constraint(
        expr=sum(
            model.tower_costs[tower] * model.build[tower]
            for tower in model.towers
        ) <= model.budget
    )
    model.total_covered_population = pyo.Objective(
        expr=sum(
            model.populations[region] * model.covered[region]
            for region in model.regions
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_covered_population))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}