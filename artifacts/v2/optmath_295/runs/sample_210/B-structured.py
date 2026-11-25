# IR: {"sets":{"locations":"1..13","zones":"1..21","coverage_by_zone":[[1,2,4,6,7,8,11],[3,4,5,6,7,9,11,13],[1,3,4,5,7,8,9,10,11],[1,4,8,10,13],[1,2,4,6,9,10],[3,4,5,6,7,8,10,13],[2,4,5,6,7,9,10,11,12,13],[5,8,11,12],[1,3,4,7,8,10,12,13],[2,4,6,8,11,12],[3,4,8,9,11],[2,4,5,7,11,12],[1,2,3,5,7,9,10,13],[1,2,6,8,9,10,12,13],[1,3,5,10],[1,5,6,8,13],[1,2,3,4,5,6,8,9,12],[1,4,6,9,11,13],[4,6,8],[1,2,3,4,5,11,13],[2,3,6,9]]},"params":{"setup_cost":"params['setup_cost']: length-13 sequence in location order, or mapping keyed by integers 1..13"},"variables":{"selected[j]":"binary for each location j"},"constraints":["For each zone z: sum(selected[j] for j in coverage_by_zone[z]) >= 1"],"objective":"minimize sum(setup_cost[j] * selected[j] for j in locations)"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve the minimum-cost emergency response center covering problem."""
    raw_costs = params["setup_cost"]

    if isinstance(raw_costs, Mapping):
        costs = {loc: raw_costs[loc] for loc in range(1, 14)}
    else:
        if len(raw_costs) != 13:
            raise ValueError("setup_cost must contain exactly 13 costs.")
        costs = {loc: raw_costs[loc - 1] for loc in range(1, 14)}

    coverage_by_zone = {
        1: (1, 2, 4, 6, 7, 8, 11),
        2: (3, 4, 5, 6, 7, 9, 11, 13),
        3: (1, 3, 4, 5, 7, 8, 9, 10, 11),
        4: (1, 4, 8, 10, 13),
        5: (1, 2, 4, 6, 9, 10),
        6: (3, 4, 5, 6, 7, 8, 10, 13),
        7: (2, 4, 5, 6, 7, 9, 10, 11, 12, 13),
        8: (5, 8, 11, 12),
        9: (1, 3, 4, 7, 8, 10, 12, 13),
        10: (2, 4, 6, 8, 11, 12),
        11: (3, 4, 8, 9, 11),
        12: (2, 4, 5, 7, 11, 12),
        13: (1, 2, 3, 5, 7, 9, 10, 13),
        14: (1, 2, 6, 8, 9, 10, 12, 13),
        15: (1, 3, 5, 10),
        16: (1, 5, 6, 8, 13),
        17: (1, 2, 3, 4, 5, 6, 8, 9, 12),
        18: (1, 4, 6, 9, 11, 13),
        19: (4, 6, 8),
        20: (1, 2, 3, 4, 5, 11, 13),
        21: (2, 3, 6, 9),
    }

    model = pyo.ConcreteModel()
    model.locations = pyo.RangeSet(1, 13)
    model.zones = pyo.RangeSet(1, 21)

    model.setup_cost = pyo.Param(
        model.locations,
        initialize=costs,
        within=pyo.Reals,
    )
    model.selected = pyo.Var(model.locations, domain=pyo.Binary)

    def coverage_rule(instance, zone):
        return sum(
            instance.selected[loc] for loc in coverage_by_zone[zone]
        ) >= 1

    model.zone_coverage = pyo.Constraint(model.zones, rule=coverage_rule)

    model.total_setup_cost = pyo.Objective(
        expr=sum(
            model.setup_cost[loc] * model.selected[loc]
            for loc in model.locations
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "A feasible solution was not found" in str(exc):
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_setup_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}