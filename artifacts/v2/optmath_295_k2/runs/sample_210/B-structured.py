# IR {
#   "sets": {"locations": "1..13", "zones": "1..21"},
#   "params": {
#     "setup_cost": "setup_cost[i] = params['setup_cost_' + str(i)] for i in locations",
#     "coverage": {
#       "1": [1, 2, 4, 6, 7, 8, 11],
#       "2": [3, 4, 5, 6, 7, 9, 11, 13],
#       "3": [1, 3, 4, 5, 7, 8, 9, 10, 11],
#       "4": [1, 4, 8, 10, 13],
#       "5": [1, 2, 4, 6, 9, 10],
#       "6": [3, 4, 5, 6, 7, 8, 10, 13],
#       "7": [2, 4, 5, 6, 7, 9, 10, 11, 12, 13],
#       "8": [5, 8, 11, 12],
#       "9": [1, 3, 4, 7, 8, 10, 12, 13],
#       "10": [2, 4, 6, 8, 11, 12],
#       "11": [3, 4, 8, 9, 11],
#       "12": [2, 4, 5, 7, 11, 12],
#       "13": [1, 2, 3, 5, 7, 9, 10, 13],
#       "14": [1, 2, 6, 8, 9, 10, 12, 13],
#       "15": [1, 3, 5, 10],
#       "16": [1, 5, 6, 8, 13],
#       "17": [1, 2, 3, 4, 5, 6, 8, 9, 12],
#       "18": [1, 4, 6, 9, 11, 13],
#       "19": [4, 6, 8],
#       "20": [1, 2, 3, 4, 5, 11, 13],
#       "21": [2, 3, 6, 9]
#     }
#   },
#   "decision_variables": {"selected[i]": {"type": "binary", "index": "locations"}},
#   "constraints": ["sum(selected[i] for i in coverage[z]) >= 1 for each z in zones"],
#   "objective": {"sense": "minimize", "expression": "sum(setup_cost[i] * selected[i] for i in locations)"}
# }

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    coverage = {
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

    setup_costs = {
        location: params[f"setup_cost_{location}"]
        for location in range(1, 14)
    }

    model = pyo.ConcreteModel()
    model.locations = pyo.RangeSet(1, 13)
    model.zones = pyo.RangeSet(1, 21)

    model.setup_cost = pyo.Param(
        model.locations,
        initialize=setup_costs,
        within=pyo.Reals,
    )
    model.coverage = pyo.Set(
        model.zones,
        within=model.locations,
        initialize=coverage,
    )
    model.selected = pyo.Var(model.locations, domain=pyo.Binary)

    def coverage_rule(instance, zone):
        return sum(
            instance.selected[location]
            for location in instance.coverage[zone]
        ) >= 1

    model.zone_coverage = pyo.Constraint(
        model.zones,
        rule=coverage_rule,
    )

    model.total_setup_cost = pyo.Objective(
        expr=sum(
            model.setup_cost[location] * model.selected[location]
            for location in model.locations
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_setup_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}