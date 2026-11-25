# IR: {"sets":{"F":"1..22","Z":"1..39","C[z]":"COVERAGE[z], the fixed facility indices below"},"params":{"facility_open_cost[f]":"params['facility_open_cost'], indexed by facility"},"variables":{"open_facility[f]":"Binary, f in F"},"constraints":["coverage[z]: sum(open_facility[f] for f in C[z]) >= 1, z in Z"],"objective":"minimize sum(facility_open_cost[f] * open_facility[f] for f in F)"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


COVERAGE = {
    1: (2, 4, 6, 7, 8, 9, 13, 21),
    2: (2, 3, 6, 8, 9, 15, 18, 19, 20, 21, 22),
    3: (1, 3, 5, 6, 8, 17, 18, 19, 20, 22),
    4: (3, 4, 5, 6, 9, 10, 11, 12, 13, 15, 16, 17, 18, 20),
    5: (1, 5, 7, 9, 10, 13, 14, 16, 17, 18, 20, 21),
    6: (1, 2, 3, 4, 5, 7, 9, 10, 16, 17, 19, 20, 21),
    7: (1, 3, 7, 8, 9, 11, 13, 14, 16, 19, 20, 21, 22),
    8: (1, 2, 6, 7, 9, 10, 13, 14, 15, 16, 17, 18, 19, 21),
    9: (1, 2, 3, 7, 8, 10, 13, 14, 15, 16, 18, 21, 22),
    10: (1, 2, 3, 4, 5, 7, 8, 9, 11, 14, 15, 16, 17, 20, 21, 22),
    11: (1, 4, 5, 7, 10, 11, 14, 16, 17, 18, 19, 21),
    12: (1, 2, 4, 5, 8, 10, 11, 13, 14, 15, 16, 17, 18, 21, 22),
    13: (1, 3, 4, 5, 6, 9, 10, 12, 14, 15, 16, 17, 19, 20, 21),
    14: (1, 4, 5, 6, 7, 8, 9, 11, 12, 16, 17, 18, 19, 20),
    15: (1, 2, 6, 7, 8, 9, 10, 11, 15, 16, 17, 20, 22),
    16: (2, 6, 8, 9, 10, 11, 12, 13, 18, 19, 22),
    17: (1, 4, 7, 8, 10, 11, 12, 15, 17, 19, 21),
    18: (1, 3, 4, 5, 7, 8, 9, 11, 12, 14, 15, 16, 17, 18, 19, 20, 21),
    19: (1, 3, 5, 6, 8, 9, 10, 12, 13, 14, 15, 17, 19, 20, 21),
    20: (1, 2, 3, 4, 8, 9, 10, 11, 13, 14, 15, 16, 17, 18, 20, 21),
    21: (1, 2, 3, 6, 8, 9, 11, 12, 14, 18, 20, 21, 22),
    22: (2, 4, 5, 7, 8, 12, 13, 14, 15, 17, 18, 20, 21),
    23: (5, 6, 8, 9, 10, 11, 16, 18, 19, 20, 21, 22),
    24: (6, 11, 14, 16, 17, 18, 20, 21, 22),
    25: (1, 2, 4, 5, 9, 10, 11, 12, 13, 14, 15, 16, 17, 19, 20, 22),
    26: (3, 4, 7, 8, 9, 10, 11, 12, 14, 15, 16, 17, 20, 22),
    27: (1, 3, 4, 6, 7, 10, 12, 13, 15, 16, 19, 20, 21, 22),
    28: (1, 2, 3, 6, 7, 8, 9, 13, 16, 18, 21, 22),
    29: (4, 6, 7, 8, 12, 16, 17, 20, 21, 22),
    30: (2, 5, 6, 7, 8, 9, 11, 13, 14, 15, 16, 17, 18, 19, 20),
    31: (2, 3, 4, 6, 7, 8, 9, 10, 11, 12, 13, 15, 16, 17, 18, 19, 20, 22),
    32: (3, 4, 5, 6, 7, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22),
    33: (3, 4, 5, 7, 10, 12, 13, 16, 18, 19, 20),
    34: (2, 5, 6, 7, 9, 11, 12, 13, 17, 19, 20, 21, 22),
    35: (3, 5, 7, 8, 10, 11, 13, 14, 15, 16, 19, 21, 22),
    36: (1, 4, 8, 9, 10, 11, 16, 18, 20, 21, 22),
    37: (1, 3, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 20, 22),
    38: (2, 4, 7, 8, 9, 10, 13, 14, 15, 16, 17, 18, 19, 21),
    39: (3, 4, 5, 6, 7, 9, 13, 14, 15, 16, 17, 18, 20, 22),
}


def solve(params):
    """
    facility_open_cost accepts either:
      - a mapping keyed by facility IDs 1..22 (integers or strings), or
      - a sequence of 22 costs, ordered by facility ID.
    """
    supplied_costs = params["facility_open_cost"]

    if isinstance(supplied_costs, Mapping):
        costs = {
            facility: supplied_costs[facility]
            if facility in supplied_costs
            else supplied_costs[str(facility)]
            for facility in range(1, 23)
        }
    else:
        if len(supplied_costs) != 22:
            raise ValueError("facility_open_cost must contain exactly 22 costs.")
        costs = {
            facility: supplied_costs[facility - 1]
            for facility in range(1, 23)
        }

    model = pyo.ConcreteModel()
    model.facilities = pyo.RangeSet(1, 22)
    model.zones = pyo.RangeSet(1, 39)

    model.facility_open_cost = pyo.Param(
        model.facilities,
        initialize=costs,
        within=pyo.Reals,
    )
    model.open_facility = pyo.Var(
        model.facilities,
        domain=pyo.Binary,
    )

    def coverage_rule(instance, zone):
        return sum(
            instance.open_facility[facility]
            for facility in COVERAGE[zone]
        ) >= 1

    model.coverage = pyo.Constraint(
        model.zones,
        rule=coverage_rule,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.facility_open_cost[facility]
            * model.open_facility[facility]
            for facility in model.facilities
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}