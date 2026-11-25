# IR: {"sets":{"regions":[0,1,2,3,4,5,6,7,8,9,10],"towers":[0,1,2,3,4,5,6]},"params":{"population":"params['population'][r]","tower_cost":"params['tower_cost'][t]","budget":"params['budget']","coverage":{"0":[1,2,4,5,6],"1":[0,1,3,6],"2":[0,1,2,4],"3":[0,1,2,3,5],"4":[0,1,2,3,5],"5":[0,1,2,6],"6":[3],"7":[3,4,6],"8":[0,2],"9":[1,3,4,5],"10":[1,3,5,6]}},"variables":{"build[t]":"Binary","covered[r]":"Binary"},"constraints":["sum(tower_cost[t]*build[t] for t in towers) <= budget","covered[r] <= sum(build[t] for t in coverage[r]) for each r in regions"],"objective":"maximize sum(population[r]*covered[r] for r in regions)"}

import pyomo.environ as pyo
from pyomo.common.errors import ApplicationError
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    coverage = {
        0: (1, 2, 4, 5, 6),
        1: (0, 1, 3, 6),
        2: (0, 1, 2, 4),
        3: (0, 1, 2, 3, 5),
        4: (0, 1, 2, 3, 5),
        5: (0, 1, 2, 6),
        6: (3,),
        7: (3, 4, 6),
        8: (0, 2),
        9: (1, 3, 4, 5),
        10: (1, 3, 5, 6),
    }

    model = pyo.ConcreteModel()
    model.regions = pyo.RangeSet(0, 10)
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

    model.budget_limit = pyo.Constraint(
        expr=sum(
            model.tower_cost[tower] * model.build[tower]
            for tower in model.towers
        ) <= model.budget
    )

    def coverage_rule(instance, region):
        return instance.covered[region] <= sum(
            instance.build[tower] for tower in coverage[region]
        )

    model.coverage_limit = pyo.Constraint(
        model.regions, rule=coverage_rule
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
    except (RuntimeError, ApplicationError):
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_coverage))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}