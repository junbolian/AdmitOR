# IR: {"sets":{"vehicles":[1,2,3,4,5],"regions":"e1..e31"},"params":{"cost_v1":"deployment cost of vehicle 1","cost_v2":"deployment cost of vehicle 2","cost_v3":"deployment cost of vehicle 3","cost_v4":"deployment cost of vehicle 4","cost_v5":"deployment cost of vehicle 5"},"coverage":{"e1":[4,5],"e2":[4,5],"e3":[3],"e4":[1,2],"e5":[1,2,4],"e6":[1,3,4],"e7":[3,4,5],"e8":[3,4],"e9":[1,2,3],"e10":[3,4,5],"e11":[3,5],"e12":[1],"e13":[1,4,5],"e14":[3,4],"e15":[1,2,5],"e16":[1,2],"e17":[2],"e18":[5],"e19":[1,4],"e20":[2],"e21":[3,4,5],"e22":[5],"e23":[1,4],"e24":[2,5],"e25":[1,3,5],"e26":[1,2,3],"e27":[5],"e28":[2,4],"e29":[1,3],"e30":[5],"e31":[1,3]},"variables":{"deploy[v]":"Binary for each vehicle v"},"constraints":["sum(deploy[v] for v in coverage[r]) >= 1 for each region r"],"objective":"minimize sum(cost_v[v] * deploy[v] for v in vehicles)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    costs = {
        1: params["cost_v1"],
        2: params["cost_v2"],
        3: params["cost_v3"],
        4: params["cost_v4"],
        5: params["cost_v5"],
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
    model.vehicles = pyo.RangeSet(1, 5)
    model.regions = pyo.Set(initialize=coverage.keys(), ordered=True)
    model.deployment_cost = pyo.Param(
        model.vehicles, initialize=costs, within=pyo.Reals
    )
    model.deploy = pyo.Var(model.vehicles, domain=pyo.Binary)

    def coverage_rule(instance, region):
        return sum(instance.deploy[vehicle] for vehicle in coverage[region]) >= 1

    model.coverage_constraints = pyo.Constraint(
        model.regions, rule=coverage_rule
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
        if "a feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}