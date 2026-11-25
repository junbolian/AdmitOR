# IR: {"sets":{"vehicles":[1,2,3,4,5,6],"routes":[1,2,3,4,5,6,7,8,9,10,11,12,13],"coverage":{"1":[6],"2":[2,4,6],"3":[1,3,4],"4":[3],"5":[1,5,6],"6":[1,4],"7":[3,5],"8":[4],"9":[3,5,6],"10":[4,5,6],"11":[3,4],"12":[1,3,5,6],"13":[3,4,6]}},"params":{"cost_vehicle_1":"real","cost_vehicle_2":"real","cost_vehicle_3":"real","cost_vehicle_4":"real","cost_vehicle_5":"real","cost_vehicle_6":"real"},"decision_variables":{"selected[vehicle]":"binary"},"constraints":["route_coverage[route]: sum(selected[vehicle] for vehicle in coverage[route]) >= 1"],"objective":"minimize sum(cost_vehicle[vehicle] * selected[vehicle] for vehicle in vehicles)"}

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
        model.vehicles, initialize=costs, within=pyo.Reals
    )
    model.selected = pyo.Var(model.vehicles, domain=pyo.Binary)

    def coverage_rule(instance, route):
        return sum(
            instance.selected[vehicle] for vehicle in coverage[route]
        ) >= 1

    model.route_coverage = pyo.Constraint(model.routes, rule=coverage_rule)
    model.total_cost = pyo.Objective(
        expr=sum(
            model.deployment_cost[vehicle] * model.selected[vehicle]
            for vehicle in model.vehicles
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "A feasible solution was not found" in str(exc):
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}