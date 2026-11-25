# IR: {"sets":{"nodes":[0,1,2,3,4,5],"routes":[0,1,2,3,4,5,6,7,8,9,10,11],"arcs":[[0,2],[0,3],[1,2],[1,3],[2,4],[2,5],[3,4],[3,5],[0,4],[0,5],[1,4],[1,5]]},"params":{"supplies":"real[nodes], from params['supplies']","arc_capacities":"real[routes], from params['arc_capacities']","arc_unit_costs":"real[routes], from params['arc_unit_costs']"},"variables":{"flow":"nonnegative continuous[routes]"},"constraints":["For each node: sum(flow on outgoing routes) - sum(flow on incoming routes) == supplies[node].","For each route: flow[route] <= arc_capacities[route]."],"objective":"Minimize sum(arc_unit_costs[route] * flow[route] for all routes)."}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    arcs = (
        (0, 2),
        (0, 3),
        (1, 2),
        (1, 3),
        (2, 4),
        (2, 5),
        (3, 4),
        (3, 5),
        (0, 4),
        (0, 5),
        (1, 4),
        (1, 5),
    )

    model = pyo.ConcreteModel()
    model.nodes = pyo.RangeSet(0, 5)
    model.routes = pyo.RangeSet(0, len(arcs) - 1)

    model.supplies = pyo.Param(
        model.nodes,
        initialize=lambda mdl, node: params["supplies"][node],
        within=pyo.Reals,
    )
    model.arc_capacities = pyo.Param(
        model.routes,
        initialize=lambda mdl, route: params["arc_capacities"][route],
        within=pyo.Reals,
    )
    model.arc_unit_costs = pyo.Param(
        model.routes,
        initialize=lambda mdl, route: params["arc_unit_costs"][route],
        within=pyo.Reals,
    )

    model.flow = pyo.Var(model.routes, domain=pyo.NonNegativeReals)

    def flow_balance_rule(mdl, node):
        outgoing = pyo.quicksum(
            mdl.flow[route]
            for route, (tail, head) in enumerate(arcs)
            if tail == node
        )
        incoming = pyo.quicksum(
            mdl.flow[route]
            for route, (tail, head) in enumerate(arcs)
            if head == node
        )
        return outgoing - incoming == mdl.supplies[node]

    model.flow_balance = pyo.Constraint(
        model.nodes,
        rule=flow_balance_rule,
    )
    model.capacity_limit = pyo.Constraint(
        model.routes,
        rule=lambda mdl, route: (
            mdl.flow[route] <= mdl.arc_capacities[route]
        ),
    )
    model.total_cost = pyo.Objective(
        expr=pyo.quicksum(
            model.arc_unit_costs[route] * model.flow[route]
            for route in model.routes
        ),
        sense=pyo.minimize,
    )

    # Appsi HiGHS raises RuntimeError when it cannot load a feasible solution.
    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}