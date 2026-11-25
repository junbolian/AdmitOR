# IR: {"sets":{"teams":[1,2,3,4,5,6,7,8,9,10,11,12,13],"zones":[1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18],"covering_teams":{"1":[3,4,6,7,9,10],"2":[1,2,3,7,11],"3":[1,5,8,9,12,13],"4":[1,3,4,5,6,7,8,9,10,13],"5":[1,2,8,9,10,11,12,13],"6":[1,7,10,13],"7":[4,5,7,8,9,11,13],"8":[2,3,6,8],"9":[1,2,3,6,7,8,9,10,12,13],"10":[1,2,3,7,8,10,11,12,13],"11":[1,2,4,5,7,8,9,10,12],"12":[1,8,9,11,12,13],"13":[2,3,4,5,6,7,10,13],"14":[1,2,5,8,9,11],"15":[4,6,8,13],"16":[1,2,3,4,6,8,10],"17":[2,11],"18":[1,2,5,10,11,12]}},"params":{"team_costs":{"source":"params['team_costs']","type":"real array of length 13","indexing":"team_costs[t-1] for team t"}},"decision_variables":{"selected[t]":{"type":"binary","indices":"t in teams"}},"constraints":["coverage[z]: sum(selected[t] for t in covering_teams[z]) >= 1 for each z in zones"],"objective":{"sense":"minimize","expression":"sum(team_costs[t-1] * selected[t] for t in teams)"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    team_costs = params["team_costs"]
    if len(team_costs) != 13:
        raise ValueError("team_costs must contain exactly 13 entries.")

    covering_teams = {
        1: (3, 4, 6, 7, 9, 10),
        2: (1, 2, 3, 7, 11),
        3: (1, 5, 8, 9, 12, 13),
        4: (1, 3, 4, 5, 6, 7, 8, 9, 10, 13),
        5: (1, 2, 8, 9, 10, 11, 12, 13),
        6: (1, 7, 10, 13),
        7: (4, 5, 7, 8, 9, 11, 13),
        8: (2, 3, 6, 8),
        9: (1, 2, 3, 6, 7, 8, 9, 10, 12, 13),
        10: (1, 2, 3, 7, 8, 10, 11, 12, 13),
        11: (1, 2, 4, 5, 7, 8, 9, 10, 12),
        12: (1, 8, 9, 11, 12, 13),
        13: (2, 3, 4, 5, 6, 7, 10, 13),
        14: (1, 2, 5, 8, 9, 11),
        15: (4, 6, 8, 13),
        16: (1, 2, 3, 4, 6, 8, 10),
        17: (2, 11),
        18: (1, 2, 5, 10, 11, 12),
    }

    model = pyo.ConcreteModel()
    model.teams = pyo.RangeSet(1, 13)
    model.zones = pyo.RangeSet(1, 18)
    model.covering_teams = pyo.Set(
        model.zones,
        within=model.teams,
        initialize=covering_teams,
    )

    model.deployment_cost = pyo.Param(
        model.teams,
        within=pyo.Reals,
        initialize={
            team: team_costs[team - 1]
            for team in model.teams
        },
    )
    model.selected = pyo.Var(model.teams, domain=pyo.Binary)

    def coverage_rule(instance, zone):
        return sum(
            instance.selected[team]
            for team in instance.covering_teams[zone]
        ) >= 1

    model.coverage = pyo.Constraint(model.zones, rule=coverage_rule)
    model.total_cost = pyo.Objective(
        expr=sum(
            model.deployment_cost[team] * model.selected[team]
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