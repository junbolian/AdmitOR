# IR: {"sets":{"Team":"1..11","Requirement":"1..20","coverage":{"1":[1,4,5],"2":[2,7,8,9,10],"3":[1,2,4,5],"4":[2,3,5,6,8,9],"5":[1,11],"6":[5,6,7,8],"7":[2,6,9],"8":[1,2,3,8,9],"9":[1,4,7],"10":[2,3,7,10],"11":[3,4,5,7,8],"12":[1,4,5,8,9,10],"13":[1,3,5,7,8,9,10],"14":[1,3,4,5,6,8,10,11],"15":[3,8,9,11],"16":[2,5,6,11],"17":[3,8,11],"18":[3,4,6,8,9,10],"19":[1,4,5,9],"20":[1,5,6,10]}},"params":{"team_cost":"real[Team], from params","req_min_teams":"real[Requirement], from params"},"variables":{"deploy":"binary[Team]"},"constraints":["coverage_requirement[r]: sum(deploy[t] for t in coverage[r]) >= req_min_teams[r], for every r in Requirement"],"objective":"minimize sum(team_cost[t] * deploy[t] for t in Team)"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.common.errors import ApplicationError
from pyomo.contrib.appsi.solvers.highs import Highs


def _indexed_value(data, position):
    """Accept one-based mappings or zero-based sequences."""
    if isinstance(data, Mapping):
        if position in data:
            return data[position]
        return data[str(position)]
    return data[position - 1]


def solve(params):
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

    cost_data = params["team_cost"]
    requirement_data = params["req_min_teams"]

    model = pyo.ConcreteModel()
    model.Team = pyo.RangeSet(1, 11)
    model.Requirement = pyo.RangeSet(1, 20)
    model.coverage = pyo.Set(
        model.Requirement,
        within=model.Team,
        initialize=coverage,
    )

    model.team_cost = pyo.Param(
        model.Team,
        within=pyo.Reals,
        initialize={
            team: _indexed_value(cost_data, team)
            for team in model.Team
        },
    )
    model.req_min_teams = pyo.Param(
        model.Requirement,
        within=pyo.Reals,
        initialize={
            requirement: _indexed_value(requirement_data, requirement)
            for requirement in model.Requirement
        },
    )

    model.deploy = pyo.Var(model.Team, domain=pyo.Binary)

    def coverage_rule(current_model, requirement):
        return (
            pyo.quicksum(
                current_model.deploy[team]
                for team in current_model.coverage[requirement]
            )
            >= current_model.req_min_teams[requirement]
        )

    model.coverage_requirement = pyo.Constraint(
        model.Requirement,
        rule=coverage_rule,
    )

    model.total_cost = pyo.Objective(
        expr=pyo.quicksum(
            model.team_cost[team] * model.deploy[team]
            for team in model.Team
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except (RuntimeError, ApplicationError):
        return {"objective": None, "status": "infeasible_or_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}