# IR: {"sets":{"T":["tower_0", "tower_1", "tower_2", "tower_3", "tower_4", "tower_5", "tower_6", "tower_7", "tower_8"],"R":["region_0", "region_1", "region_2", "region_3", "region_4", "region_5", "region_6", "region_7", "region_8", "region_9", "region_10"],"C":{"region_0":[4,5,6,8],"region_1":[1,2,3,4,5,7],"region_2":[3,5,7],"region_3":[1,3,4,5,6],"region_4":[0,3,4,7],"region_5":[5,7,8],"region_6":[1,3,6,8],"region_7":[6,7],"region_8":[3],"region_9":[0,2,3,4,5,8],"region_10":[1,2,4,6,7,8]}},"params":{"tower_cost":"T -> params['tower_cost']","budget":"params['budget']","population":"R -> params['population']"},"variables":{"build[t]":"Binary, t in T","covered[r]":"Binary, r in R"},"constraints":["sum(tower_cost[t]*build[t] for t in T) <= budget","covered[r] <= sum(build[t] for t in C[r]), r in R","covered[r] >= build[t], r in R, t in C[r]"],"objective":"maximize sum(population[r]*covered[r] for r in R)"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def _indexed_value(values, label, position):
    """Accept sequences or mappings keyed by entity name or integer index."""
    if isinstance(values, Mapping) and label in values:
        return values[label]
    return values[position]


def solve(params):
    tower_cost = params["tower_cost"]
    budget = params["budget"]
    population = params["population"]

    towers = tuple(f"tower_{idx}" for idx in range(9))
    regions = tuple(f"region_{idx}" for idx in range(11))

    coverage_indices = (
        (4, 5, 6, 8),
        (1, 2, 3, 4, 5, 7),
        (3, 5, 7),
        (1, 3, 4, 5, 6),
        (0, 3, 4, 7),
        (5, 7, 8),
        (1, 3, 6, 8),
        (6, 7),
        (3,),
        (0, 2, 3, 4, 5, 8),
        (1, 2, 4, 6, 7, 8),
    )
    coverage = {
        regions[region_idx]: tuple(towers[tower_idx] for tower_idx in neighbors)
        for region_idx, neighbors in enumerate(coverage_indices)
    }

    model = pyo.ConcreteModel()

    model.T = pyo.Set(initialize=towers, ordered=True)
    model.R = pyo.Set(initialize=regions, ordered=True)
    model.C = pyo.Set(
        model.R,
        within=model.T,
        initialize=lambda mdl, region: coverage[region],
    )
    model.coverage_pairs = pyo.Set(
        dimen=2,
        initialize=[
            (region, tower)
            for region in regions
            for tower in coverage[region]
        ],
    )

    model.tower_cost = pyo.Param(
        model.T,
        initialize={
            tower: _indexed_value(tower_cost, tower, idx)
            for idx, tower in enumerate(towers)
        },
    )
    model.budget = pyo.Param(initialize=budget)
    model.population = pyo.Param(
        model.R,
        initialize={
            region: _indexed_value(population, region, idx)
            for idx, region in enumerate(regions)
        },
    )

    model.build = pyo.Var(model.T, domain=pyo.Binary)
    model.covered = pyo.Var(model.R, domain=pyo.Binary)

    model.construction_budget = pyo.Constraint(
        expr=sum(
            model.tower_cost[tower] * model.build[tower]
            for tower in model.T
        )
        <= model.budget
    )

    model.coverage_requires_tower = pyo.Constraint(
        model.R,
        rule=lambda mdl, region: mdl.covered[region]
        <= sum(mdl.build[tower] for tower in mdl.C[region]),
    )

    model.built_tower_covers_region = pyo.Constraint(
        model.coverage_pairs,
        rule=lambda mdl, region, tower: mdl.covered[region]
        >= mdl.build[tower],
    )

    model.total_covered_population = pyo.Objective(
        expr=sum(
            model.population[region] * model.covered[region]
            for region in model.R
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "A feasible solution was not found" not in str(exc):
            raise
        return {"objective": None, "status": "no_feasible_solution"}

    try:
        obj_val = float(pyo.value(model.total_covered_population))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}