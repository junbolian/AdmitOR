# IR: {"sets":{"trucks":"0..5","routes":"0..5"},"params":{"cost_matrix":"6x6 transportation costs from params['cost_matrix']"},"variables":{"assignment[truck,route]":"Binary"},"constraints":["For each truck: sum(assignment[truck,route] for route in routes) == 1","For each route: sum(assignment[truck,route] for truck in trucks) == 1"],"objective":"Minimize sum(cost_matrix[truck][route] * assignment[truck,route] for truck in trucks for route in routes)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost_matrix = params["cost_matrix"]

    model = pyo.ConcreteModel()
    model.trucks = pyo.RangeSet(0, 5)
    model.routes = pyo.RangeSet(0, 5)

    model.transport_cost = pyo.Param(
        model.trucks,
        model.routes,
        initialize=lambda mdl, truck, route: cost_matrix[truck][route],
        within=pyo.Reals,
    )

    model.assignment = pyo.Var(
        model.trucks,
        model.routes,
        domain=pyo.Binary,
    )

    def truck_assignment_rule(mdl, truck):
        return sum(
            mdl.assignment[truck, route] for route in mdl.routes
        ) == 1

    model.truck_assignment = pyo.Constraint(
        model.trucks,
        rule=truck_assignment_rule,
    )

    def route_assignment_rule(mdl, route):
        return sum(
            mdl.assignment[truck, route] for truck in mdl.trucks
        ) == 1

    model.route_assignment = pyo.Constraint(
        model.routes,
        rule=route_assignment_rule,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.transport_cost[truck, route]
            * model.assignment[truck, route]
            for truck in model.trucks
            for route in model.routes
        ),
        sense=pyo.minimize,
    )

    failure_reason = "objective_unavailable"
    try:
        Highs().solve(model)
    except RuntimeError:
        failure_reason = "solve_failed"

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": failure_reason}

    return {"objective": obj_val, "status": "optimal"}