# IR: {"sets":{"A":"0..24","T":"0..17"},"params":{"population":"nonnegative[A]","tower_cost":"nonnegative[T]","budget":"nonnegative scalar","coverage":"binary[A,T]"},"variables":{"build":"binary[T]","covered":"binary[A]"},"constraints":["sum(tower_cost[t]*build[t] for t in T) <= budget","covered[a] <= sum(coverage[a,t]*build[t] for t in T) for each a in A"],"objective":"maximize sum(population[a]*covered[a] for a in A)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    population = params["population"]
    tower_cost = params["tower_cost"]
    budget = params["budget"]
    coverage = params["coverage"]

    model = pyo.ConcreteModel()

    model.areas = pyo.RangeSet(0, 24)
    model.towers = pyo.RangeSet(0, 17)

    model.population = pyo.Param(
        model.areas,
        initialize={area: population[area] for area in model.areas},
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
    model.coverage = pyo.Param(
        model.areas,
        model.towers,
        initialize={
            (area, tower): coverage[area][tower]
            for area in model.areas
            for tower in model.towers
        },
        within=pyo.Binary,
    )

    model.build = pyo.Var(model.towers, domain=pyo.Binary)
    model.covered = pyo.Var(model.areas, domain=pyo.Binary)

    model.budget_limit = pyo.Constraint(
        expr=sum(
            model.tower_cost[tower] * model.build[tower]
            for tower in model.towers
        ) <= model.budget
    )

    def coverage_rule(instance, area):
        return instance.covered[area] <= sum(
            instance.coverage[area, tower] * instance.build[tower]
            for tower in instance.towers
        )

    model.coverage_limit = pyo.Constraint(
        model.areas,
        rule=coverage_rule,
    )

    model.total_population = pyo.Objective(
        expr=sum(
            model.population[area] * model.covered[area]
            for area in model.areas
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        # HiGHS may raise when no solution is available to load.
        # Objective retrieval below is the sole success criterion.
        pass

    try:
        obj_val = float(pyo.value(model.total_population))
    except (ValueError, TypeError):
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}