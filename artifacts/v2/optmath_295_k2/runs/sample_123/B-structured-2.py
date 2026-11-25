# IR: {"sets":{"regions":"0..9","towers":"0..6","coverage":{"0":[0,3,5,6],"1":[2,3,4,6],"2":[0,1,4,5,6],"3":[0,3,4],"4":[0,3,4],"5":[1,2,3],"6":[1,2,3,4],"7":[1,2,3,4,5,6],"8":[0,1,2,4,5],"9":[1,4,6]}},"params":{"population":"params['population'][r]","tower_cost":"params['tower_cost'][t]","budget":"params['budget']"},"variables":{"build[t]":"binary","covered[r]":"binary"},"constraints":["sum(tower_cost[t]*build[t] for t in towers) <= budget","covered[r] <= sum(build[t] for t in coverage[r]) for each region r"],"objective":"maximize sum(population[r]*covered[r] for r in regions)"}

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

    model.population = pyo.Param(
        model.regions,
        initialize={
            region: params["population"][region]
            for region in range(10)
        },
    )
    model.tower_cost = pyo.Param(
        model.towers,
        initialize={
            tower: params["tower_cost"][tower]
            for tower in range(7)
        },
    )
    model.budget = pyo.Param(initialize=params["budget"])

    model.build = pyo.Var(model.towers, domain=pyo.Binary)
    model.covered = pyo.Var(model.regions, domain=pyo.Binary)

    model.budget_constraint = pyo.Constraint(
        expr=sum(
            model.tower_cost[tower] * model.build[tower]
            for tower in model.towers
        ) <= model.budget
    )

    def coverage_rule(model, region):
        return model.covered[region] <= sum(
            model.build[tower] for tower in coverage[region]
        )

    model.coverage_constraint = pyo.Constraint(
        model.regions, rule=coverage_rule
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
    except RuntimeError as exc:
        # APPsi raises this when no feasible solution can be loaded.
        # Still use objective retrieval as the sole success test.
        if "A feasible solution was not found" not in str(exc):
            raise

    try:
        obj_val = float(pyo.value(model.total_population))
    except ValueError:
        return {"objective": None, "status": "no_solution"}

    return {"objective": obj_val, "status": "optimal"}