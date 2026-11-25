# IR: {"sets":{"teams":"1..14","locations":"1..21","cover":{"1":[2,5,6,7,8,9,11,14],"2":[2,5,7,13],"3":[1,2,4,5,6,9,10,12,13],"4":[3,6,13,14],"5":[2,6,10],"6":[4,6,8,14],"7":[1,4,5,8,10,11,12,13,14],"8":[1,5,11,14],"9":[1,2,3,6,7,10,11,12],"10":[6,11,12,13],"11":[1,3,4,6,7,9],"12":[1,3,5,8,9],"13":[1,4,9,11,12,13,14],"14":[2,4,7,8,13],"15":[5,7,8,9],"16":[1,5,6,8,11,13],"17":[1,4,5,6,8,14],"18":[3,8,10,11,12,14],"19":[2,5,7,12,13],"20":[1,3,4,5,10,11,13],"21":[1,8,12,14]}},"params":{"cost[t]":"params['team_costs']: 14-element sequence in team order, or mapping keyed by team numbers or their strings","requirement[l]":"params['location_'+str(l)+'_requirement'] for l=1..21"},"variables":{"selected[t]":"Binary for t in teams"},"constraints":["coverage[l]: sum(selected[t] for t in cover[l]) >= requirement[l], for l in locations"],"objective":"minimize sum(cost[t]*selected[t] for t in teams)"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    coverage = {
        1: (2, 5, 6, 7, 8, 9, 11, 14),
        2: (2, 5, 7, 13),
        3: (1, 2, 4, 5, 6, 9, 10, 12, 13),
        4: (3, 6, 13, 14),
        5: (2, 6, 10),
        6: (4, 6, 8, 14),
        7: (1, 4, 5, 8, 10, 11, 12, 13, 14),
        8: (1, 5, 11, 14),
        9: (1, 2, 3, 6, 7, 10, 11, 12),
        10: (6, 11, 12, 13),
        11: (1, 3, 4, 6, 7, 9),
        12: (1, 3, 5, 8, 9),
        13: (1, 4, 9, 11, 12, 13, 14),
        14: (2, 4, 7, 8, 13),
        15: (5, 7, 8, 9),
        16: (1, 5, 6, 8, 11, 13),
        17: (1, 4, 5, 6, 8, 14),
        18: (3, 8, 10, 11, 12, 14),
        19: (2, 5, 7, 12, 13),
        20: (1, 3, 4, 5, 10, 11, 13),
        21: (1, 8, 12, 14),
    }

    raw_costs = params["team_costs"]
    if isinstance(raw_costs, Mapping):
        costs = {
            team: raw_costs[team] if team in raw_costs else raw_costs[str(team)]
            for team in range(1, 15)
        }
    else:
        if len(raw_costs) != 14:
            raise ValueError("team_costs must contain exactly 14 costs.")
        costs = {team: raw_costs[team - 1] for team in range(1, 15)}

    requirements = {
        location: params[f"location_{location}_requirement"]
        for location in range(1, 22)
    }

    model = pyo.ConcreteModel()
    model.teams = pyo.RangeSet(1, 14)
    model.locations = pyo.RangeSet(1, 21)

    model.cost = pyo.Param(
        model.teams,
        initialize=costs,
        within=pyo.Reals,
    )
    model.requirement = pyo.Param(
        model.locations,
        initialize=requirements,
        within=pyo.Reals,
    )
    model.selected = pyo.Var(model.teams, domain=pyo.Binary)

    def coverage_rule(instance, location):
        return (
            sum(instance.selected[team] for team in coverage[location])
            >= instance.requirement[location]
        )

    model.coverage_constraints = pyo.Constraint(
        model.locations,
        rule=coverage_rule,
    )
    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost[team] * model.selected[team]
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
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}