# IR: {"sets":{"hubs":[1,2,3,4,5,6,7,8,9,10,11,12,13,14,15],"routes":[1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16],"service_hubs":{"1":[2,3,4,7,11,13],"2":[10,12,15],"3":[1,5,6,8,11,12,13,14],"4":[2,3,4,6,7,10,12,14],"5":[1,2,3,10,13],"6":[1,2,3,6,8,10,11,12,14],"7":[3,4,5,7,8,10,11,13,14],"8":[1,2,3,7,9,12,13],"9":[1,4,7,10,12,13,14],"10":[1,3,4,5,7,10,11,13,14,15],"11":[1,4,7,9,13,14],"12":[3,4,6,8,10,11,12,13,14,15],"13":[1,2,4,5,7,11,13,14],"14":[1,4,5,6,9,12,14,15],"15":[2,6,7,12,13,14],"16":[1,4,8,11,12,14,15]}},"params":{"hub_costs":{"source":"params['hub_costs']","type":"real array of length 15","indexing":"hub h uses array position h-1"}},"decision_variables":{"hub_active[h]":"binary for every hub h"},"constraints":["For every route r: sum(hub_active[h] for h in service_hubs[r]) >= 1"],"objective":{"sense":"minimize","expression":"sum(hub_costs[h-1] * hub_active[h] for h in hubs)"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    hub_costs = params["hub_costs"]
    if len(hub_costs) != 15:
        raise ValueError("params['hub_costs'] must contain exactly 15 costs.")

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
        initialize={hub: hub_costs[hub - 1] for hub in model.hubs},
        within=pyo.Reals,
    )
    model.hub_active = pyo.Var(model.hubs, domain=pyo.Binary)

    def coverage_rule(instance, route):
        return (
            sum(instance.hub_active[hub] for hub in service_hubs[route]) >= 1
        )

    model.route_coverage = pyo.Constraint(
        model.routes,
        rule=coverage_rule,
    )
    model.total_cost = pyo.Objective(
        expr=sum(
            model.activation_cost[hub] * model.hub_active[hub]
            for hub in model.hubs
        ),
        sense=pyo.minimize,
    )

    failure_reason = "no_solution"
    try:
        Highs().solve(model)
    except RuntimeError:
        # APPSI can raise when no solution can be loaded.
        # Determine success exclusively by objective retrieval below.
        failure_reason = "solver_failed"

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": failure_reason}

    return {"objective": obj_val, "status": "optimal"}