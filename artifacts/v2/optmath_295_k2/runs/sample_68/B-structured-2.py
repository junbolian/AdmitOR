# IR: {
#   "sets": {"vehicles": [1, 2, 3, 4, 5, 6], "routes": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]},
#   "params": ["cost_vehicle_1", "cost_vehicle_2", "cost_vehicle_3", "cost_vehicle_4", "cost_vehicle_5", "cost_vehicle_6"],
#   "decision_variables": {"selected[v]": "binary for every v in vehicles"},
#   "constraints": [
#     "route_1: selected[6] >= 1",
#     "route_2: selected[2] + selected[4] + selected[6] >= 1",
#     "route_3: selected[1] + selected[3] + selected[4] >= 1",
#     "route_4: selected[3] >= 1",
#     "route_5: selected[1] + selected[5] + selected[6] >= 1",
#     "route_6: selected[1] + selected[4] >= 1",
#     "route_7: selected[3] + selected[5] >= 1",
#     "route_8: selected[4] >= 1",
#     "route_9: selected[3] + selected[5] + selected[6] >= 1",
#     "route_10: selected[4] + selected[5] + selected[6] >= 1",
#     "route_11: selected[3] + selected[4] >= 1",
#     "route_12: selected[1] + selected[3] + selected[5] + selected[6] >= 1",
#     "route_13: selected[3] + selected[4] + selected[6] >= 1"
#   ],
#   "objective": "minimize sum(cost_vehicle_v * selected[v] for v in vehicles)"
# }

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    costs = {
        1: params["cost_vehicle_1"],
        2: params["cost_vehicle_2"],
        3: params["cost_vehicle_3"],
        4: params["cost_vehicle_4"],
        5: params["cost_vehicle_5"],
        6: params["cost_vehicle_6"],
    }

    coverage = {
        1: (6,),
        2: (2, 4, 6),
        3: (1, 3, 4),
        4: (3,),
        5: (1, 5, 6),
        6: (1, 4),
        7: (3, 5),
        8: (4,),
        9: (3, 5, 6),
        10: (4, 5, 6),
        11: (3, 4),
        12: (1, 3, 5, 6),
        13: (3, 4, 6),
    }

    model = pyo.ConcreteModel()
    model.vehicles = pyo.RangeSet(1, 6)
    model.routes = pyo.RangeSet(1, 13)
    model.deployment_cost = pyo.Param(
        model.vehicles,
        initialize=costs,
        within=pyo.Reals,
    )
    model.selected = pyo.Var(model.vehicles, domain=pyo.Binary)

    def coverage_rule(instance, route):
        return sum(
            instance.selected[vehicle] for vehicle in coverage[route]
        ) >= 1

    model.route_coverage = pyo.Constraint(
        model.routes,
        rule=coverage_rule,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.deployment_cost[vehicle] * model.selected[vehicle]
            for vehicle in model.vehicles
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