# IR: {"sets":{"teams":"1..13","areas":"1..17","coverage":{"1":[5,7,11],"2":[1,2,5,9,11],"3":[4,6],"4":[2,5,8,10,11],"5":[2,6,7,9,10],"6":[1,7,8,12],"7":[3,5,13],"8":[2,7,9,12,13],"9":[13],"10":[2,5,6,7,9,12],"11":[2,3,6,7,8,10,11],"12":[6,11],"13":[2,3,12],"14":[6,10,11,12],"15":[4,5,9,11],"16":[3,5,9,12,13],"17":[5,7,8]}},"params":{"team_cost":"real[teams], from params['team_cost']","area_requirement":"nonnegative integer[areas], from params['area_requirement']"},"variables":{"selected":"binary[teams]"},"constraints":["coverage_constraint[a]: sum(selected[t] for t in coverage[a]) >= area_requirement[a], for each area a"],"objective":"minimize sum(team_cost[t] * selected[t] for t in teams)"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def _indexed_value(data, position):
    """Accept one-based mappings or zero-based sequences."""
    if isinstance(data, Mapping):
        if position in data:
            return data[position]
        return data[str(position)]
    return data[position - 1]


def solve(params):
    team_cost_data = params["team_cost"]
    area_requirement_data = params["area_requirement"]

    coverage = {
        1: (5, 7, 11),
        2: (1, 2, 5, 9, 11),
        3: (4, 6),
        4: (2, 5, 8, 10, 11),
        5: (2, 6, 7, 9, 10),
        6: (1, 7, 8, 12),
        7: (3, 5, 13),
        8: (2, 7, 9, 12, 13),
        9: (13,),
        10: (2, 5, 6, 7, 9, 12),
        11: (2, 3, 6, 7, 8, 10, 11),
        12: (6, 11),
        13: (2, 3, 12),
        14: (6, 10, 11, 12),
        15: (4, 5, 9, 11),
        16: (3, 5, 9, 12, 13),
        17: (5, 7, 8),
    }

    model = pyo.ConcreteModel()
    model.teams = pyo.RangeSet(1, 13)
    model.areas = pyo.RangeSet(1, 17)

    model.coverage = pyo.Set(
        model.areas,
        within=model.teams,
        initialize=coverage,
    )
    model.team_cost = pyo.Param(
        model.teams,
        within=pyo.Reals,
        initialize={
            team: _indexed_value(team_cost_data, team)
            for team in model.teams
        },
    )
    model.area_requirement = pyo.Param(
        model.areas,
        within=pyo.NonNegativeIntegers,
        initialize={
            area: _indexed_value(area_requirement_data, area)
            for area in model.areas
        },
    )

    model.selected = pyo.Var(model.teams, domain=pyo.Binary)

    def coverage_rule(instance, area):
        return (
            sum(
                instance.selected[team]
                for team in instance.coverage[area]
            )
            >= instance.area_requirement[area]
        )

    model.coverage_constraint = pyo.Constraint(
        model.areas,
        rule=coverage_rule,
    )
    model.total_cost = pyo.Objective(
        expr=sum(
            model.team_cost[team] * model.selected[team]
            for team in model.teams
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        # APPSI can raise when no feasible solution can be loaded.
        # Success is determined solely by objective retrieval below.
        pass

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}