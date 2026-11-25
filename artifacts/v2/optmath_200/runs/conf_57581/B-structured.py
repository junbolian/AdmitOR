# IR: {"sets":{"locations":[1,2,3,4,5,6,7,8,9,10,11,12],"rows":[1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21]},"params":{"selection_cost":"12-element sequence, in location order","coverage_requirement":"21-element sequence, in constraint order"},"variables":{"selected[i]":"binary for each location i"},"constraints":{"coverage[r]":"sum(selected[i] for i in coverage_locations[r]) >= coverage_requirement[r]"},"coverage_locations":[[2,6,8,10,11,12],[7,9,11,12],[2,5,7,9,10,12],[1,2,3,5,6,10,11,12],[4,7,10,11,12],[1,2,3,4],[1,2,3,6,7,8],[1,3,5,7,12],[4,5,8,9,10],[5,6,10],[2,5,9,12],[2,3,4,5,8],[2,3,6,7],[7,8],[2,6,7,9],[1,3,6,8,12],[3,4,5,6,12],[4,7,8,11],[3,4,6,7,10],[1,3,6,8],[1,3,4,7,9,10]],"objective":"minimize sum(selection_cost[i] * selected[i] for i in locations)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    selection_cost = params["selection_cost"]
    coverage_requirement = params["coverage_requirement"]

    if len(selection_cost) != 12:
        raise ValueError("selection_cost must contain 12 entries.")
    if len(coverage_requirement) != 21:
        raise ValueError("coverage_requirement must contain 21 entries.")

    coverage_locations = (
        (2, 6, 8, 10, 11, 12),
        (7, 9, 11, 12),
        (2, 5, 7, 9, 10, 12),
        (1, 2, 3, 5, 6, 10, 11, 12),
        (4, 7, 10, 11, 12),
        (1, 2, 3, 4),
        (1, 2, 3, 6, 7, 8),
        (1, 3, 5, 7, 12),
        (4, 5, 8, 9, 10),
        (5, 6, 10),
        (2, 5, 9, 12),
        (2, 3, 4, 5, 8),
        (2, 3, 6, 7),
        (7, 8),
        (2, 6, 7, 9),
        (1, 3, 6, 8, 12),
        (3, 4, 5, 6, 12),
        (4, 7, 8, 11),
        (3, 4, 6, 7, 10),
        (1, 3, 6, 8),
        (1, 3, 4, 7, 9, 10),
    )

    model = pyo.ConcreteModel()
    model.locations = pyo.RangeSet(1, 12)
    model.rows = pyo.RangeSet(1, 21)

    model.selection_cost = pyo.Param(
        model.locations,
        initialize={i: selection_cost[i - 1] for i in model.locations},
        within=pyo.Reals,
    )
    model.coverage_requirement = pyo.Param(
        model.rows,
        initialize={r: coverage_requirement[r - 1] for r in model.rows},
        within=pyo.Reals,
    )
    model.selected = pyo.Var(model.locations, domain=pyo.Binary)

    def coverage_rule(instance, r):
        return (
            sum(instance.selected[i] for i in coverage_locations[r - 1])
            >= instance.coverage_requirement[r]
        )

    model.coverage = pyo.Constraint(model.rows, rule=coverage_rule)
    model.total_cost = pyo.Objective(
        expr=sum(
            model.selection_cost[i] * model.selected[i]
            for i in model.locations
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}