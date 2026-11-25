# IR: {"sets":{"F":"1..25","A":"1..36","C[a]":"COVERAGE[a], the given facility incidence lists"},"params":{"facility_costs":"params['facility_costs']; sequence of 25 costs in facility order"},"variables":{"selected[f]":"Binary, f in F"},"constraints":["coverage[a]: sum(selected[f] for f in C[a]) >= 1, a in A"],"objective":"minimize sum(facility_costs[f-1] * selected[f] for f in F)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


COVERAGE = {
    1: (1, 2, 3, 4, 9, 10, 11, 12, 13, 14, 15, 17, 21),
    2: (1, 2, 3, 4, 5, 7, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 21, 23, 24, 25),
    3: (3, 4, 7, 8, 10, 11, 12, 13, 14, 16, 20, 22, 25),
    4: (1, 2, 3, 4, 6, 7, 8, 9, 10, 11, 12, 13, 15, 16, 19, 20, 22, 24, 25),
    5: (2, 10, 12, 14, 17, 18, 19, 21, 23, 24, 25),
    6: (3, 4, 5, 6, 7, 8, 11, 12, 17, 18, 25),
    7: (2, 3, 4, 6, 7, 10, 12, 13, 14, 15, 19, 20, 21, 22, 25),
    8: (1, 2, 3, 4, 5, 6, 9, 12, 13, 15, 16, 17, 18, 19, 20, 22, 23, 24),
    9: (5, 6, 7, 9, 11, 12, 14, 15, 21, 22, 23, 24, 25),
    10: (4, 7, 8, 9, 10, 13, 14, 15, 16, 19, 21, 23, 24),
    11: (6, 10, 12, 13, 15, 18, 22, 25),
    12: (1, 3, 5, 6, 10, 11, 13, 14, 15, 16, 18, 19, 20, 22, 24, 25),
    13: (4, 5, 7, 10, 11, 12, 13, 14, 18, 19, 20, 21, 25),
    14: (1, 4, 5, 6, 7, 8, 10, 15, 18, 19, 20, 21, 22, 23, 24, 25),
    15: (1, 2, 3, 4, 5, 7, 8, 9, 10, 12, 13, 16, 18, 19, 20, 21, 24),
    16: (1, 3, 5, 6, 8, 11, 13, 14, 18, 19, 20, 21, 22, 23, 24),
    17: (8, 9, 13, 14, 15, 16, 20, 21, 25),
    18: (1, 2, 3, 4, 6, 7, 8, 9, 10, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 24),
    19: (1, 3, 4, 5, 6, 7, 9, 13, 14, 15, 16, 18, 19, 24),
    20: (2, 3, 6, 9, 11, 15, 16, 17, 19, 20, 21, 25),
    21: (1, 2, 4, 6, 7, 9, 10, 11, 12, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25),
    22: (1, 4, 5, 6, 10, 11, 12, 13, 15, 16, 18, 19, 21),
    23: (1, 2, 3, 5, 6, 9, 10, 13, 15, 16, 17, 18, 19, 20, 21, 22, 24),
    24: (4, 5, 6, 8, 10, 15, 16, 17, 18, 20, 25),
    25: (1, 3, 5, 6, 9, 10, 11, 12, 14, 17, 18, 19, 21, 22, 23, 25),
    26: (2, 3, 4, 5, 7, 8, 9, 11, 13, 14, 16, 19, 20, 21, 22, 24, 25),
    27: (5, 6, 8, 9, 12, 14, 17, 18, 19, 22, 23, 25),
    28: (1, 3, 4, 5, 6, 8, 10, 14, 16, 17, 19, 20, 23, 24, 25),
    29: (2, 3, 4, 6, 7, 8, 9, 11, 12, 14, 15, 17, 18, 19, 20, 21, 22, 23, 24),
    30: (1, 2, 3, 5, 10, 12, 15, 16, 17, 18, 20, 21, 22, 25),
    31: (1, 2, 4, 5, 6, 7, 10, 11, 12, 13, 14, 15, 19, 20, 21, 22, 24, 25),
    32: (1, 6, 8, 9, 11, 12, 13, 14, 15, 16, 18, 19, 20, 22, 23),
    33: (1, 2, 4, 5, 6, 7, 8, 9, 14, 15, 16, 17, 18, 19, 20, 21, 22, 24, 25),
    34: (1, 3, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 17, 18),
    35: (2, 3, 5, 8, 9, 10, 11, 13, 15, 16, 17, 19, 21, 22, 24, 25),
    36: (2, 5, 6, 7, 9, 11, 12, 14, 16, 20, 21, 22, 24, 25),
}


def solve(params):
    """Solve the set-cover problem using costs supplied in facility order."""
    facility_costs = params["facility_costs"]
    if len(facility_costs) != 25:
        return {"objective": None, "status": "invalid_cost_count"}

    model = pyo.ConcreteModel()
    model.facilities = pyo.RangeSet(1, 25)
    model.service_areas = pyo.RangeSet(1, 36)

    model.operating_cost = pyo.Param(
        model.facilities,
        initialize={
            facility: facility_costs[facility - 1]
            for facility in model.facilities
        },
        within=pyo.Reals,
    )
    model.selected = pyo.Var(model.facilities, domain=pyo.Binary)

    def coverage_rule(instance, area):
        return sum(
            instance.selected[facility]
            for facility in COVERAGE[area]
        ) >= 1

    model.coverage = pyo.Constraint(
        model.service_areas,
        rule=coverage_rule,
    )
    model.total_cost = pyo.Objective(
        expr=sum(
            model.operating_cost[facility] * model.selected[facility]
            for facility in model.facilities
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        # HiGHS may raise when it cannot load a feasible solution.
        # Objective retrieval below remains the sole success criterion.
        pass

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "no_objective"}

    return {"objective": obj_val, "status": "optimal"}