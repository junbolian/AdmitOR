# IR: {"sets":{"facilities":"1..22","zones":"1..39","coverage":"fixed zone-to-facility incidence in coverage_by_zone"},"params":{"facility_cost":"real cost indexed by facility, read from params['facility_cost']"},"variables":{"open_facility[i]":"binary for every facility i"},"constraints":["For every zone z: sum(open_facility[i] for i in coverage_by_zone[z]) >= 1"],"objective":{"sense":"minimize","expression":"sum(facility_cost[i] * open_facility[i] for i in facilities)"}}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve facility coverage using a 22-element cost sequence or facility-ID mapping."""
    coverage_by_zone = {
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

    supplied_costs = params["facility_cost"]
    if isinstance(supplied_costs, Mapping):
        facility_costs = {
            facility: supplied_costs[facility]
            if facility in supplied_costs
            else supplied_costs[str(facility)]
            for facility in range(1, 23)
        }
    else:
        if len(supplied_costs) != 22:
            raise ValueError("facility_cost must contain exactly 22 costs.")
        facility_costs = {
            facility: supplied_costs[facility - 1]
            for facility in range(1, 23)
        }

    model = pyo.ConcreteModel()
    model.facilities = pyo.RangeSet(1, 22)
    model.zones = pyo.RangeSet(1, 39)
    model.facility_cost = pyo.Param(
        model.facilities,
        initialize=facility_costs,
        within=pyo.Reals,
    )
    model.open_facility = pyo.Var(model.facilities, domain=pyo.Binary)

    def coverage_rule(instance, zone):
        return sum(
            instance.open_facility[facility]
            for facility in coverage_by_zone[zone]
        ) >= 1

    model.zone_coverage = pyo.Constraint(model.zones, rule=coverage_rule)
    model.total_cost = pyo.Objective(
        expr=sum(
            model.facility_cost[facility] * model.open_facility[facility]
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
    except ValueError:
        return {"objective": None, "status": "no_objective"}

    return {"objective": obj_val, "status": "optimal"}