# IR: {"sets":{"teams":"1..13","areas":"1..17","coverage":{"1":[5,7,11],"2":[1,2,5,9,11],"3":[4,6],"4":[2,5,8,10,11],"5":[2,6,7,9,10],"6":[1,7,8,12],"7":[3,5,13],"8":[2,7,9,12,13],"9":[13],"10":[2,5,6,7,9,12],"11":[2,3,6,7,8,10,11],"12":[6,11],"13":[2,3,12],"14":[6,10,11,12],"15":[4,5,9,11],"16":[3,5,9,12,13],"17":[5,7,8]}},"params":{"team_costs":"numeric sequence of length 13, ordered by team","area_requirements":"numeric sequence of length 17, ordered by area"},"decision_variables":{"selected[team]":"Binary"},"constraints":["For each area: sum(selected[team] for team in coverage[area]) >= area_requirements[area-1]"],"objective":"Minimize sum(team_costs[team-1] * selected[team] for team in teams)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve using sequences ordered Team 1..13 and Area 1..17."""
    team_costs = params["team_costs"]
    area_requirements = params["area_requirements"]

    if len(team_costs) != 13:
        raise ValueError("team_costs must contain exactly 13 entries.")
    if len(area_requirements) != 17:
        raise ValueError("area_requirements must contain exactly 17 entries.")

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

    model.deployment_cost = pyo.Param(
        model.teams,
        initialize={team: team_costs[team - 1] for team in model.teams},
        within=pyo.Reals,
    )
    model.required_coverage = pyo.Param(
        model.areas,
        initialize={
            area: area_requirements[area - 1] for area in model.areas
        },
        within=pyo.Reals,
    )
    model.selected = pyo.Var(model.teams, domain=pyo.Binary)

    def coverage_rule(instance, area):
        return (
            sum(instance.selected[team] for team in coverage[area])
            >= instance.required_coverage[area]
        )

    model.coverage_constraints = pyo.Constraint(
        model.areas, rule=coverage_rule
    )
    model.total_cost = pyo.Objective(
        expr=sum(
            model.deployment_cost[team] * model.selected[team]
            for team in model.teams
        ),
        sense=pyo.minimize,
    )

    failure_reason = "objective_unavailable"
    try:
        Highs().solve(model)
    except RuntimeError as error:
        if "a feasible solution was not found" not in str(error).lower():
            raise
        failure_reason = "no_feasible_solution"

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": failure_reason}

    return {"objective": obj_val, "status": "optimal"}