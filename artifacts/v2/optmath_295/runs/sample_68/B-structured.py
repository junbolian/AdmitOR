# IR: {
#   "sets": {"vehicles": [1,2,3,4,5,6], "routes": [1,2,3,4,5,6,7,8,9,10,11,12,13]},
#   "params": {"vehicle_cost_1": "real", "vehicle_cost_2": "real", "vehicle_cost_3": "real", "vehicle_cost_4": "real", "vehicle_cost_5": "real", "vehicle_cost_6": "real"},
#   "coverage": {"1": [6], "2": [2,4,6], "3": [1,3,4], "4": [3], "5": [1,5,6], "6": [1,4], "7": [3,5], "8": [4], "9": [3,5,6], "10": [4,5,6], "11": [3,4], "12": [1,3,5,6], "13": [3,4,6]},
#   "decision_variables": {"deploy[v]": {"type": "binary", "index": "v in vehicles"}},
#   "constraints": ["route_coverage[r]: sum(deploy[v] for v in coverage[r]) >= 1, for every r in routes"],
#   "objective": {"sense": "minimize", "expression": "sum(vehicle_cost_v * deploy[v] for v in vehicles)"}
# }

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    costs = {
        1: params["vehicle_cost_1"],
        2: params["vehicle_cost_2"],
        3: params["vehicle_cost_3"],
        4: params["vehicle_cost_4"],
        5: params["vehicle_cost_5"],
        6: params["vehicle_cost_6"],
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
    model.deploy = pyo.Var(model.vehicles, domain=pyo.Binary)

    def route_coverage_rule(instance, route):
        return sum(
            instance.deploy[vehicle] for vehicle in coverage[route]
        ) >= 1

    model.route_coverage = pyo.Constraint(
        model.routes,
        rule=route_coverage_rule,
    )
    model.total_cost = pyo.Objective(
        expr=sum(
            model.deployment_cost[vehicle] * model.deploy[vehicle]
            for vehicle in model.vehicles
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPsi raises this when it cannot load a feasible solution.
        if "a feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}