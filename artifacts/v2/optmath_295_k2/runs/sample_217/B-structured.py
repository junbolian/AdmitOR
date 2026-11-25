# IR: {"sets":{"teams":"1..11","requirements":"1..20","coverage":{"1":[1,4,5],"2":[2,7,8,9,10],"3":[1,2,4,5],"4":[2,3,5,6,8,9],"5":[1,11],"6":[5,6,7,8],"7":[2,6,9],"8":[1,2,3,8,9],"9":[1,4,7],"10":[2,3,7,10],"11":[3,4,5,7,8],"12":[1,4,5,8,9,10],"13":[1,3,5,7,8,9,10],"14":[1,3,4,5,6,8,10,11],"15":[3,8,9,11],"16":[2,5,6,11],"17":[3,8,11],"18":[3,4,6,8,9,10],"19":[1,4,5,9],"20":[1,5,6,10]}},"params":{"team_costs":"real array of length 11, read from params['team_costs']","requirement_thresholds":"real array of length 20, read from params['requirement_thresholds']"},"decision_variables":{"deploy[t]":"binary for each team t"},"constraints":["For every requirement r: sum(deploy[t] for t in coverage[r]) >= requirement_thresholds[r-1]."],"objective":"Minimize sum(team_costs[t-1] * deploy[t] for t in teams)."}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    team_costs = params["team_costs"]
    requirement_thresholds = params["requirement_thresholds"]

    if len(team_costs) != 11 or len(requirement_thresholds) != 20:
        return {"objective": None, "status": "invalid_parameter_lengths"}

    coverage = {
        1: (1, 4, 5),
        2: (2, 7, 8, 9, 10),
        3: (1, 2, 4, 5),
        4: (2, 3, 5, 6, 8, 9),
        5: (1, 11),
        6: (5, 6, 7, 8),
        7: (2, 6, 9),
        8: (1, 2, 3, 8, 9),
        9: (1, 4, 7),
        10: (2, 3, 7, 10),
        11: (3, 4, 5, 7, 8),
        12: (1, 4, 5, 8, 9, 10),
        13: (1, 3, 5, 7, 8, 9, 10),
        14: (1, 3, 4, 5, 6, 8, 10, 11),
        15: (3, 8, 9, 11),
        16: (2, 5, 6, 11),
        17: (3, 8, 11),
        18: (3, 4, 6, 8, 9, 10),
        19: (1, 4, 5, 9),
        20: (1, 5, 6, 10),
    }

    model = pyo.ConcreteModel()
    model.teams = pyo.RangeSet(1, 11)
    model.requirements = pyo.RangeSet(1, 20)

    model.deployment_cost = pyo.Param(
        model.teams,
        initialize={t: team_costs[t - 1] for t in model.teams},
        within=pyo.Reals,
    )
    model.minimum_coverage = pyo.Param(
        model.requirements,
        initialize={
            r: requirement_thresholds[r - 1] for r in model.requirements
        },
        within=pyo.Reals,
    )

    model.deploy = pyo.Var(model.teams, domain=pyo.Binary)

    def coverage_rule(instance, r):
        return (
            sum(instance.deploy[t] for t in coverage[r])
            >= instance.minimum_coverage[r]
        )

    model.coverage_constraints = pyo.Constraint(
        model.requirements, rule=coverage_rule
    )
    model.total_cost = pyo.Objective(
        expr=sum(
            model.deployment_cost[t] * model.deploy[t]
            for t in model.teams
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "infeasible_or_solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}