# IR: {"sets":{"vehicles":[1,2,3,4,5],"regions":["e1","e2","e3","e4","e5","e6","e7","e8","e9","e10","e11","e12","e13","e14","e15","e16","e17","e18","e19","e20","e21","e22","e23","e24","e25","e26","e27","e28","e29","e30","e31"]},"params":{"cost_vehicle_1":"params['cost_vehicle_1']","cost_vehicle_2":"params['cost_vehicle_2']","cost_vehicle_3":"params['cost_vehicle_3']","cost_vehicle_4":"params['cost_vehicle_4']","cost_vehicle_5":"params['cost_vehicle_5']"},"coverage":{"e1":[4,5],"e2":[4,5],"e3":[3],"e4":[1,2],"e5":[1,2,4],"e6":[1,3,4],"e7":[3,4,5],"e8":[3,4],"e9":[1,2,3],"e10":[3,4,5],"e11":[3,5],"e12":[1],"e13":[1,4,5],"e14":[3,4],"e15":[1,2,5],"e16":[1,2],"e17":[2],"e18":[5],"e19":[1,4],"e20":[2],"e21":[3,4,5],"e22":[5],"e23":[1,4],"e24":[2,5],"e25":[1,3,5],"e26":[1,2,3],"e27":[5],"e28":[2,4],"e29":[1,3],"e30":[5],"e31":[1,3]},"decision_variables":{"deploy[v]":{"type":"binary","index":"v in vehicles"}},"constraints":["For each r in regions: sum(deploy[v] for v in coverage[r]) >= 1"],"objective":{"sense":"minimize","expression":"sum(cost_vehicle_v * deploy[v] for v in vehicles)"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    vehicle_costs = {
        1: params["cost_vehicle_1"],
        2: params["cost_vehicle_2"],
        3: params["cost_vehicle_3"],
        4: params["cost_vehicle_4"],
        5: params["cost_vehicle_5"],
    }

    coverage = {
        "e1": (4, 5),
        "e2": (4, 5),
        "e3": (3,),
        "e4": (1, 2),
        "e5": (1, 2, 4),
        "e6": (1, 3, 4),
        "e7": (3, 4, 5),
        "e8": (3, 4),
        "e9": (1, 2, 3),
        "e10": (3, 4, 5),
        "e11": (3, 5),
        "e12": (1,),
        "e13": (1, 4, 5),
        "e14": (3, 4),
        "e15": (1, 2, 5),
        "e16": (1, 2),
        "e17": (2,),
        "e18": (5,),
        "e19": (1, 4),
        "e20": (2,),
        "e21": (3, 4, 5),
        "e22": (5,),
        "e23": (1, 4),
        "e24": (2, 5),
        "e25": (1, 3, 5),
        "e26": (1, 2, 3),
        "e27": (5,),
        "e28": (2, 4),
        "e29": (1, 3),
        "e30": (5,),
        "e31": (1, 3),
    }

    model = pyo.ConcreteModel()
    model.vehicles = pyo.Set(initialize=(1, 2, 3, 4, 5), ordered=True)
    model.regions = pyo.Set(initialize=coverage.keys(), ordered=True)
    model.vehicle_cost = pyo.Param(
        model.vehicles,
        initialize=vehicle_costs,
        within=pyo.Reals,
    )
    model.deploy = pyo.Var(model.vehicles, domain=pyo.Binary)

    def coverage_rule(current_model, region):
        return sum(
            current_model.deploy[vehicle] for vehicle in coverage[region]
        ) >= 1

    model.region_coverage = pyo.Constraint(
        model.regions,
        rule=coverage_rule,
    )
    model.total_cost = pyo.Objective(
        expr=sum(
            model.vehicle_cost[vehicle] * model.deploy[vehicle]
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
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}