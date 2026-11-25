# IR: {"sets":{"teams":[1,2,3,4,5,6,7,8,9,10],"locations":[1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17],"coverage":{"1":[1,2,4,5,6,7,9],"2":[1,3,4,5,6,9,10],"3":[1,2,3,4,8,10],"4":[2,5,8,10],"5":[1,7],"6":[1,2,3,5,8,9,10],"7":[1,2,4,5,9],"8":[3,8,9],"9":[3,4,5,7],"10":[1,2,5,6],"11":[2,3,7,9],"12":[5,7,8,9,10],"13":[2,3,8,10],"14":[1,2,3,5,6,9,10],"15":[2,6,8,9],"16":[2,3,5,7,10],"17":[1,2,3,5,8,9,10]}},"params":{"team_costs":"length-10 sequence from params[\"team_costs\"]; position t-1 is team t's cost"},"variables":{"deploy[t]":{"type":"binary","index":"teams"}},"constraints":["For each location l: sum(deploy[t] for t in coverage[l]) >= 1"],"objective":{"sense":"minimize","expression":"sum(team_costs[t-1] * deploy[t] for t in teams)"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    team_costs = params["team_costs"]
    if len(team_costs) != 10:
        raise ValueError("team_costs must contain exactly 10 deployment costs.")

    coverage = {
        1: (1, 2, 4, 5, 6, 7, 9),
        2: (1, 3, 4, 5, 6, 9, 10),
        3: (1, 2, 3, 4, 8, 10),
        4: (2, 5, 8, 10),
        5: (1, 7),
        6: (1, 2, 3, 5, 8, 9, 10),
        7: (1, 2, 4, 5, 9),
        8: (3, 8, 9),
        9: (3, 4, 5, 7),
        10: (1, 2, 5, 6),
        11: (2, 3, 7, 9),
        12: (5, 7, 8, 9, 10),
        13: (2, 3, 8, 10),
        14: (1, 2, 3, 5, 6, 9, 10),
        15: (2, 6, 8, 9),
        16: (2, 3, 5, 7, 10),
        17: (1, 2, 3, 5, 8, 9, 10),
    }

    model = pyo.ConcreteModel()
    model.teams = pyo.RangeSet(1, 10)
    model.locations = pyo.RangeSet(1, 17)

    model.deployment_cost = pyo.Param(
        model.teams,
        initialize={team: team_costs[team - 1] for team in model.teams},
        within=pyo.Reals,
    )
    model.deploy = pyo.Var(model.teams, domain=pyo.Binary)

    def coverage_rule(mdl, location):
        return sum(mdl.deploy[team] for team in coverage[location]) >= 1

    model.coverage_requirement = pyo.Constraint(
        model.locations,
        rule=coverage_rule,
    )
    model.total_cost = pyo.Objective(
        expr=sum(
            model.deployment_cost[team] * model.deploy[team]
            for team in model.teams
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