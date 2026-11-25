# IR: {"sets":{"regions":"0..10","towers":"0..6","covering_towers":{"0":[1,2,4,5,6],"1":[0,1,3,6],"2":[0,1,2,4],"3":[0,1,2,3,5],"4":[0,1,2,3,5],"5":[0,1,2,6],"6":[3],"7":[3,4,6],"8":[0,2],"9":[1,3,4,5],"10":[1,3,5,6]}},"params":{"population":"params['population'][r]","tower_cost":"params['tower_cost'][t]","budget":"params['budget']"},"variables":{"build[t]":"binary","covered[r]":"binary"},"constraints":["sum(tower_cost[t]*build[t] for t in towers) <= budget","covered[r] <= sum(build[t] for t in covering_towers[r]) for each region r"],"objective":"maximize sum(population[r]*covered[r] for r in regions)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    covering_towers = {
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
        initialize={r: params["population"][r] for r in model.regions},
    )
    model.tower_cost = pyo.Param(
        model.towers,
        initialize={t: params["tower_cost"][t] for t in model.towers},
    )
    model.budget = pyo.Param(initialize=params["budget"])

    model.build = pyo.Var(model.towers, domain=pyo.Binary)
    model.covered = pyo.Var(model.regions, domain=pyo.Binary)

    model.budget_limit = pyo.Constraint(
        expr=sum(
            model.tower_cost[t] * model.build[t] for t in model.towers
        ) <= model.budget
    )

    def coverage_rule(instance, r):
        return instance.covered[r] <= sum(
            instance.build[t] for t in covering_towers[r]
        )

    model.coverage_link = pyo.Constraint(
        model.regions, rule=coverage_rule
    )

    model.total_coverage = pyo.Objective(
        expr=sum(
            model.population[r] * model.covered[r]
            for r in model.regions
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
        return {"objective": None, "status": "no_objective"}

    return {"objective": obj_val, "status": "optimal"}