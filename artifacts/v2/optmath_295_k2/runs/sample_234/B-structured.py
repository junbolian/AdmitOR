# IR: {"sets":{"areas":"0..24","towers":"0..17"},"params":{"population":"nonnegative vector indexed by areas, from params['population']","tower_cost":"nonnegative vector indexed by towers, from params['tower_cost']","budget":"scalar from params['budget']","coverage":"binary areas-by-towers matrix from params['coverage']"},"variables":{"build[t]":"binary for each tower t","covered[a]":"binary for each area a"},"constraints":["sum(tower_cost[t]*build[t] for t in towers) <= budget","covered[a] <= sum(coverage[a,t]*build[t] for t in towers), for each area a"],"objective":"maximize sum(population[a]*covered[a] for a in areas)"}

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
    model.budget = pyo.Param(initialize=budget, within=pyo.Reals)
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
        model.areas, rule=coverage_rule
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
    except RuntimeError as exc:
        # APPSI raises this when no feasible solution can be loaded.
        if "A feasible solution was not found" not in str(exc):
            raise

    try:
        obj_val = float(pyo.value(model.total_population))
    except (ValueError, TypeError):
        return {"objective": None, "status": "no_solution"}

    return {"objective": obj_val, "status": "optimal"}