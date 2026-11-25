# IR: {"sets":{"hubs":"1..15","routes":"1..16","service_hubs":{"1":[2,3,4,7,11,13],"2":[10,12,15],"3":[1,5,6,8,11,12,13,14],"4":[2,3,4,6,7,10,12,14],"5":[1,2,3,10,13],"6":[1,2,3,6,8,10,11,12,14],"7":[3,4,5,7,8,10,11,13,14],"8":[1,2,3,7,9,12,13],"9":[1,4,7,10,12,13,14],"10":[1,3,4,5,7,10,11,13,14,15],"11":[1,4,7,9,13,14],"12":[3,4,6,8,10,11,12,13,14,15],"13":[1,2,4,5,7,11,13,14],"14":[1,4,5,6,9,12,14,15],"15":[2,6,7,12,13,14],"16":[1,4,8,11,12,14,15]}},"params":{"hub_activation_costs":"15 costs in hub order, read from params"},"variables":{"activate_hub[h]":"Binary for h in hubs"},"constraints":["For each route r: sum(activate_hub[h] for h in service_hubs[r]) >= 1"],"objective":"Minimize sum(hub_activation_costs[h-1] * activate_hub[h] for h in hubs)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    costs = params["hub_activation_costs"]
    if len(costs) != 15:
        raise ValueError("hub_activation_costs must contain exactly 15 costs.")

    service_hubs = {
        1: (2, 3, 4, 7, 11, 13),
        2: (10, 12, 15),
        3: (1, 5, 6, 8, 11, 12, 13, 14),
        4: (2, 3, 4, 6, 7, 10, 12, 14),
        5: (1, 2, 3, 10, 13),
        6: (1, 2, 3, 6, 8, 10, 11, 12, 14),
        7: (3, 4, 5, 7, 8, 10, 11, 13, 14),
        8: (1, 2, 3, 7, 9, 12, 13),
        9: (1, 4, 7, 10, 12, 13, 14),
        10: (1, 3, 4, 5, 7, 10, 11, 13, 14, 15),
        11: (1, 4, 7, 9, 13, 14),
        12: (3, 4, 6, 8, 10, 11, 12, 13, 14, 15),
        13: (1, 2, 4, 5, 7, 11, 13, 14),
        14: (1, 4, 5, 6, 9, 12, 14, 15),
        15: (2, 6, 7, 12, 13, 14),
        16: (1, 4, 8, 11, 12, 14, 15),
    }

    model = pyo.ConcreteModel()
    model.hubs = pyo.RangeSet(1, 15)
    model.routes = pyo.RangeSet(1, 16)
    model.activation_cost = pyo.Param(
        model.hubs,
        initialize={hub: costs[hub - 1] for hub in model.hubs},
        within=pyo.Reals,
    )
    model.activate_hub = pyo.Var(model.hubs, domain=pyo.Binary)

    def route_coverage_rule(instance, route):
        return sum(
            instance.activate_hub[hub] for hub in service_hubs[route]
        ) >= 1

    model.route_coverage = pyo.Constraint(
        model.routes, rule=route_coverage_rule
    )
    model.total_activation_cost = pyo.Objective(
        expr=sum(
            model.activation_cost[hub] * model.activate_hub[hub]
            for hub in model.hubs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_activation_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}