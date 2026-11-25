# IR: {"sets":{"R":"0..9","T":"0..7","C":{"0":[0,3,5,7],"1":[2,6],"2":[1,3,5],"3":[0,2,5,6,7],"4":[4,6],"5":[0,1,2,5,6],"6":[1,3,4,6],"7":[0,1,6],"8":[4,5,6,7],"9":[3,4,5,6]}},"params":{"population":"nonnegative[R], from params['population']","tower_cost":"nonnegative[T], from params['tower_cost']","budget":"nonnegative scalar, from params['budget']"},"variables":{"build":"binary[T]","covered":"binary[R]"},"constraints":["sum(tower_cost[t]*build[t] for t in T) <= budget","covered[r] <= sum(build[t] for t in C[r]) for each r in R","covered[r] == 1 for each r in R"],"objective":"maximize sum(population[r]*covered[r] for r in R)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve the mandatory-coverage tower selection problem.

    population and tower_cost must be sequences or mappings indexed by integers.
    Because every region must be covered, every feasible solution attains
    the total population as its objective value.
    """
    population = params["population"]
    tower_cost = params["tower_cost"]
    budget = params["budget"]

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
    model.regions = pyo.RangeSet(0, 9)
    model.towers = pyo.RangeSet(0, 7)

    model.population = pyo.Param(
        model.regions,
        initialize={region: population[region] for region in model.regions},
        within=pyo.NonNegativeReals,
    )
    model.tower_cost = pyo.Param(
        model.towers,
        initialize={tower: tower_cost[tower] for tower in model.towers},
        within=pyo.NonNegativeReals,
    )
    model.budget = pyo.Param(
        initialize=budget,
        within=pyo.NonNegativeReals,
    )

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

    model.coverage_link = pyo.Constraint(
        model.regions, rule=coverage_rule
    )
    model.mandatory_coverage = pyo.Constraint(
        model.regions,
        rule=lambda instance, region: instance.covered[region] == 1,
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
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_population))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}