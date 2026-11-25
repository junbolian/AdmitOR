# IR: {"sets":{"teams":"1..12","locations":"1..18","coverage":{"1":[4,8,10,11],"2":[2,3,7,8,10],"3":[1,4,6],"4":[8,10,12],"5":[1,3,4,8,11],"6":[1,2,6,7,8,12],"7":[1,2,4,6,9,11],"8":[2,7,8,11],"9":[2,3,4,6],"10":[2,3,5,6,9,10,11,12],"11":[2,3,4,10],"12":[4,5,9,10,11],"13":[7,9,12],"14":[1,7,9,11],"15":[6,7,8,9,10],"16":[1,4,6,7,9,10,12],"17":[4,5,7,8,10,12],"18":[1,5,8,9]}},"params":{"deployment_costs":"params['deployment_costs']: length-12 sequence in team order","coverage_requirements":"params['coverage_requirements']: length-18 sequence in location order"},"variables":{"deploy[team]":"Binary"},"constraints":["For each location: sum(deploy[team] for team in coverage[location]) >= coverage_requirements[location-1]"],"objective":"Minimize sum(deployment_costs[team-1] * deploy[team] for team in teams)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    deployment_costs = params["deployment_costs"]
    coverage_requirements = params["coverage_requirements"]

    if len(deployment_costs) != 12:
        raise ValueError("deployment_costs must contain exactly 12 values.")
    if len(coverage_requirements) != 18:
        raise ValueError("coverage_requirements must contain exactly 18 values.")

    coverage = {
        1: (4, 8, 10, 11),
        2: (2, 3, 7, 8, 10),
        3: (1, 4, 6),
        4: (8, 10, 12),
        5: (1, 3, 4, 8, 11),
        6: (1, 2, 6, 7, 8, 12),
        7: (1, 2, 4, 6, 9, 11),
        8: (2, 7, 8, 11),
        9: (2, 3, 4, 6),
        10: (2, 3, 5, 6, 9, 10, 11, 12),
        11: (2, 3, 4, 10),
        12: (4, 5, 9, 10, 11),
        13: (7, 9, 12),
        14: (1, 7, 9, 11),
        15: (6, 7, 8, 9, 10),
        16: (1, 4, 6, 7, 9, 10, 12),
        17: (4, 5, 7, 8, 10, 12),
        18: (1, 5, 8, 9),
    }

    model = pyo.ConcreteModel()
    model.teams = pyo.RangeSet(1, 12)
    model.locations = pyo.RangeSet(1, 18)

    model.team_cost = pyo.Param(
        model.teams,
        initialize={
            team: deployment_costs[team - 1]
            for team in model.teams
        },
        within=pyo.Reals,
    )
    model.required_coverage = pyo.Param(
        model.locations,
        initialize={
            location: coverage_requirements[location - 1]
            for location in model.locations
        },
        within=pyo.Reals,
    )

    model.deploy = pyo.Var(model.teams, domain=pyo.Binary)

    def coverage_rule(instance, location):
        return (
            pyo.quicksum(
                instance.deploy[team] for team in coverage[location]
            )
            >= instance.required_coverage[location]
        )

    model.coverage_constraints = pyo.Constraint(
        model.locations, rule=coverage_rule
    )

    model.total_cost = pyo.Objective(
        expr=pyo.quicksum(
            model.team_cost[team] * model.deploy[team]
            for team in model.teams
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}