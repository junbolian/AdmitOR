# IR: {"sets":{"regions":[0,1,2,3,4,5,6,7,8,9,10,11],"towers":[0,1,2,3,4,5,6,7,8]},"params":{"population":"params['population'][r]","tower_cost":"params['tower_cost'][t]","budget":"params['budget']","serves":{"0":[4,6,8],"1":[2,5,7],"2":[0,3,4,5,6,7,8],"3":[0,2,3,7],"4":[0,1,4,5,7],"5":[1,2],"6":[0,1,3,4,5,6,8],"7":[3,4,6,8],"8":[1,2,3,6,8],"9":[1,5,8],"10":[3,5,6],"11":[0,2,3,4,5,8]}},"variables":{"build[t]":"binary","covered[r]":"binary"},"constraints":["covered[r] <= sum(build[t] for t in serves[r]) for each region r","sum(tower_cost[t]*build[t] for t in towers) <= budget"],"objective":"maximize sum(population[r]*covered[r] for r in regions)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    serves = {
        0: (4, 6, 8),
        1: (2, 5, 7),
        2: (0, 3, 4, 5, 6, 7, 8),
        3: (0, 2, 3, 7),
        4: (0, 1, 4, 5, 7),
        5: (1, 2),
        6: (0, 1, 3, 4, 5, 6, 8),
        7: (3, 4, 6, 8),
        8: (1, 2, 3, 6, 8),
        9: (1, 5, 8),
        10: (3, 5, 6),
        11: (0, 2, 3, 4, 5, 8),
    }

    model = pyo.ConcreteModel()
    model.regions = pyo.RangeSet(0, 11)
    model.towers = pyo.RangeSet(0, 8)

    model.population = pyo.Param(
        model.regions,
        initialize={r: params["population"][r] for r in model.regions},
    )
    model.tower_cost = pyo.Param(
        model.towers,
        initialize={t: params["tower_cost"][t] for t in model.towers},
    )
    model.budget = pyo.Param(initialize=params["budget"])

    model.build = pyo.Var(model.towers, domain=pyo.Binary)
    model.covered = pyo.Var(model.regions, domain=pyo.Binary)

    def coverage_rule(instance, r):
        return instance.covered[r] <= sum(
            instance.build[t] for t in serves[r]
        )

    model.coverage_requirement = pyo.Constraint(
        model.regions, rule=coverage_rule
    )
    model.budget_limit = pyo.Constraint(
        expr=sum(
            model.tower_cost[t] * model.build[t] for t in model.towers
        ) <= model.budget
    )
    model.total_coverage = pyo.Objective(
        expr=sum(
            model.population[r] * model.covered[r] for r in model.regions
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