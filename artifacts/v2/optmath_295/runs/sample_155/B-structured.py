# IR: {"sets":{"teams":[1,2,3,4,5,6,7,8,9,10],"locations":[1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17],"coverage":{"1":[1,2,4,5,6,7,9],"2":[1,3,4,5,6,9,10],"3":[1,2,3,4,8,10],"4":[2,5,8,10],"5":[1,7],"6":[1,2,3,5,8,9,10],"7":[1,2,4,5,9],"8":[3,8,9],"9":[3,4,5,7],"10":[1,2,5,6],"11":[2,3,7,9],"12":[5,7,8,9,10],"13":[2,3,8,10],"14":[1,2,3,5,6,9,10],"15":[2,6,8,9],"16":[2,3,5,7,10],"17":[1,2,3,5,8,9,10]}},"params":{"team_costs":{"source":"params['team_costs']: sequence position team-1, or mapping key team (integer or string)","indexed_by":"teams","type":"real"}},"decision_variables":{"deploy":{"indexed_by":"teams","type":"binary"}},"constraints":["For each location: sum(deploy[team] for team in coverage[location]) >= 1."],"objective":{"sense":"minimize","expression":"sum(team_costs[team] * deploy[team] for team in teams)"}}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Accept costs as a ten-element sequence or a mapping keyed by team IDs."""
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

    raw_costs = params["team_costs"]
    if isinstance(raw_costs, Mapping):
        costs = {
            team: raw_costs[team] if team in raw_costs else raw_costs[str(team)]
            for team in range(1, 11)
        }
    else:
        costs = {
            team: raw_costs[team - 1]
            for team in range(1, 11)
        }

    model = pyo.ConcreteModel()
    model.teams = pyo.RangeSet(1, 10)
    model.locations = pyo.RangeSet(1, 17)

    model.team_costs = pyo.Param(
        model.teams,
        initialize=costs,
        within=pyo.Reals,
    )
    model.deploy = pyo.Var(model.teams, domain=pyo.Binary)

    def coverage_rule(instance, location):
        return sum(
            instance.deploy[team] for team in coverage[location]
        ) >= 1

    model.coverage_constraints = pyo.Constraint(
        model.locations,
        rule=coverage_rule,
    )
    model.total_cost = pyo.Objective(
        expr=sum(
            model.team_costs[team] * model.deploy[team]
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