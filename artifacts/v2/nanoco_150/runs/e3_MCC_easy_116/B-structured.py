# IR: {"sets":{"warehouses":[0,1,2,3,4,5],"routes":[[0,1],[0,2],[0,5],[1,0],[1,2],[1,5],[2,1],[2,3],[2,5],[3,0],[3,1],[3,2],[3,4],[4,3],[4,5],[5,0],[5,2],[5,4]]},"params":{"route_cost":"params['route_cost'][r]","route_min":"params['route_min'][r]","route_max":"params['route_max'][r]"},"variables":{"shipment[r]":"nonnegative integer"},"constraints":["shipment[r] >= route_min[r] for every route r","shipment[r] <= route_max[r] for every route r","sum(shipment[r] for routes entering w) == sum(shipment[r] for routes leaving w) for every warehouse w"],"objective":"minimize sum(route_cost[r] * shipment[r] for every route r)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    routes = (
        (0, 1), (0, 2), (0, 5),
        (1, 0), (1, 2), (1, 5),
        (2, 1), (2, 3), (2, 5),
        (3, 0), (3, 1), (3, 2), (3, 4),
        (4, 3), (4, 5),
        (5, 0), (5, 2), (5, 4),
    )

    route_cost = params["route_cost"]
    route_min = params["route_min"]
    route_max = params["route_max"]

    model = pyo.ConcreteModel()
    model.warehouses = pyo.RangeSet(0, 5)
    model.route_ids = pyo.RangeSet(0, 17)

    model.route_cost = pyo.Param(
        model.route_ids,
        initialize={r: route_cost[r] for r in range(len(routes))},
        within=pyo.Reals,
    )
    model.route_min = pyo.Param(
        model.route_ids,
        initialize={r: route_min[r] for r in range(len(routes))},
        within=pyo.Reals,
    )
    model.route_max = pyo.Param(
        model.route_ids,
        initialize={r: route_max[r] for r in range(len(routes))},
        within=pyo.Reals,
    )

    model.shipment = pyo.Var(
        model.route_ids,
        domain=pyo.NonNegativeIntegers,
    )

    def minimum_rule(mdl, r):
        return mdl.shipment[r] >= mdl.route_min[r]

    def capacity_rule(mdl, r):
        return mdl.shipment[r] <= mdl.route_max[r]

    def balance_rule(mdl, warehouse):
        incoming = sum(
            mdl.shipment[r]
            for r, (_, destination) in enumerate(routes)
            if destination == warehouse
        )
        outgoing = sum(
            mdl.shipment[r]
            for r, (origin, _) in enumerate(routes)
            if origin == warehouse
        )
        return incoming == outgoing

    model.minimum_obligation = pyo.Constraint(
        model.route_ids, rule=minimum_rule
    )
    model.route_capacity = pyo.Constraint(
        model.route_ids, rule=capacity_rule
    )
    model.warehouse_balance = pyo.Constraint(
        model.warehouses, rule=balance_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.route_cost[r] * model.shipment[r]
            for r in model.route_ids
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "infeasible_or_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}