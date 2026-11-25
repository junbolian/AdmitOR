# IR: {"sets":{"V":[1,2,3,4,5],"R":[1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31]},"params":{"cost_v1":"real","cost_v2":"real","cost_v3":"real","cost_v4":"real","cost_v5":"real"},"coverage":{"1":[4,5],"2":[4,5],"3":[3],"4":[1,2],"5":[1,2,4],"6":[1,3,4],"7":[3,4,5],"8":[3,4],"9":[1,2,3],"10":[3,4,5],"11":[3,5],"12":[1],"13":[1,4,5],"14":[3,4],"15":[1,2,5],"16":[1,2],"17":[2],"18":[5],"19":[1,4],"20":[2],"21":[3,4,5],"22":[5],"23":[1,4],"24":[2,5],"25":[1,3,5],"26":[1,2,3],"27":[5],"28":[2,4],"29":[1,3],"30":[5],"31":[1,3]},"variables":{"x[v]":"binary for each v in V"},"constraints":["sum(x[v] for v in coverage[r]) >= 1 for each r in R"],"objective":"minimize sum(cost_v[v] * x[v] for v in V)"}

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
        1: (4, 5),
        2: (4, 5),
        3: (3,),
        4: (1, 2),
        5: (1, 2, 4),
        6: (1, 3, 4),
        7: (3, 4, 5),
        8: (3, 4),
        9: (1, 2, 3),
        10: (3, 4, 5),
        11: (3, 5),
        12: (1,),
        13: (1, 4, 5),
        14: (3, 4),
        15: (1, 2, 5),
        16: (1, 2),
        17: (2,),
        18: (5,),
        19: (1, 4),
        20: (2,),
        21: (3, 4, 5),
        22: (5,),
        23: (1, 4),
        24: (2, 5),
        25: (1, 3, 5),
        26: (1, 2, 3),
        27: (5,),
        28: (2, 4),
        29: (1, 3),
        30: (5,),
        31: (1, 3),
    }

    model = pyo.ConcreteModel()
    model.vehicles = pyo.RangeSet(1, 5)
    model.regions = pyo.RangeSet(1, 31)

    model.deployment_cost = pyo.Param(
        model.vehicles,
        initialize=costs,
        within=pyo.Reals,
    )
    model.x = pyo.Var(model.vehicles, domain=pyo.Binary)

    def coverage_rule(current_model, region):
        return sum(
            current_model.x[vehicle] for vehicle in coverage[region]
        ) >= 1

    model.coverage_constraints = pyo.Constraint(
        model.regions,
        rule=coverage_rule,
    )
    model.total_cost = pyo.Objective(
        expr=sum(
            model.deployment_cost[vehicle] * model.x[vehicle]
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