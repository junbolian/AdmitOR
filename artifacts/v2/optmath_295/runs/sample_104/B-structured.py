# IR: {"sets":{"R":"range(params['num_regions']), frozen size 10","T":"range(params['num_towers']), frozen size 8","C":{"0":[0,3,5,7],"1":[2,6],"2":[1,3,5],"3":[0,2,5,6,7],"4":[4,6],"5":[0,1,2,5,6],"6":[1,3,4,6],"7":[0,1,6],"8":[4,5,6,7],"9":[3,4,5,6]}},"params":{"populations":"population[r], r in R","tower_costs":"cost[t], t in T","budget":"total construction budget","num_regions":"frozen region count","num_towers":"frozen tower count"},"variables":{"build[t]":"Binary, t in T","covered[r]":"Binary, r in R"},"constraints":["sum(cost[t]*build[t] for t in T) <= budget","covered[r] <= sum(build[t] for t in C[r]), for each r in R","covered[r] == 1, for each r in R"],"objective":"maximize sum(population[r]*covered[r] for r in R)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    populations = params["populations"]
    tower_costs = params["tower_costs"]
    budget = params["budget"]
    num_regions = params["num_regions"]
    num_towers = params["num_towers"]

    if num_regions != 10 or num_towers != 8:
        return {"objective": None, "status": "invalid_dimensions"}

    coverage = {
        0: (0, 3, 5, 7),
        1: (2, 6),
        2: (1, 3, 5),
        3: (0, 2, 5, 6, 7),
        4: (4, 6),
        5: (0, 1, 2, 5, 6),
        6: (1, 3, 4, 6),
        7: (0, 1, 6),
        8: (4, 5, 6, 7),
        9: (3, 4, 5, 6),
    }

    model = pyo.ConcreteModel()
    model.regions = pyo.RangeSet(0, num_regions - 1)
    model.towers = pyo.RangeSet(0, num_towers - 1)

    model.population = pyo.Param(
        model.regions,
        initialize={r: populations[r] for r in model.regions},
    )
    model.construction_cost = pyo.Param(
        model.towers,
        initialize={t: tower_costs[t] for t in model.towers},
    )
    model.budget_limit = pyo.Param(initialize=budget)

    model.build = pyo.Var(model.towers, domain=pyo.Binary)
    model.covered = pyo.Var(model.regions, domain=pyo.Binary)

    model.budget_constraint = pyo.Constraint(
        expr=sum(
            model.construction_cost[t] * model.build[t]
            for t in model.towers
        ) <= model.budget_limit
    )

    def coverage_rule(mod, r):
        return mod.covered[r] <= sum(
            mod.build[t] for t in coverage[r]
        )

    model.coverage_constraint = pyo.Constraint(
        model.regions, rule=coverage_rule
    )

    # Mandatory coverage makes the objective constant for feasible solutions.
    model.required_coverage = pyo.Constraint(
        model.regions,
        rule=lambda mod, r: mod.covered[r] == 1,
    )

    model.total_population = pyo.Objective(
        expr=sum(
            model.population[r] * model.covered[r]
            for r in model.regions
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPsi raises this error when no feasible solution can be loaded.
        # Other runtime errors are unexpected and must propagate.
        if "a feasible solution was not found" not in str(exc).lower():
            raise

    try:
        obj_val = float(pyo.value(model.total_population))
    except ValueError:
        return {"objective": None, "status": "no_solution"}

    return {"objective": obj_val, "status": "optimal"}