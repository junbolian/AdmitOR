# IR: {"sets":{"teams":"1..13","areas":"1..17","coverage":{"1":[5,7,11],"2":[1,2,5,9,11],"3":[4,6],"4":[2,5,8,10,11],"5":[2,6,7,9,10],"6":[1,7,8,12],"7":[3,5,13],"8":[2,7,9,12,13],"9":[13],"10":[2,5,6,7,9,12],"11":[2,3,6,7,8,10,11],"12":[6,11],"13":[2,3,12],"14":[6,10,11,12],"15":[4,5,9,11],"16":[3,5,9,12,13],"17":[5,7,8]}},"params":{"team_costs":"params['team_costs']: length-13 sequence; team t uses position t-1","area_requirements":"params['area_requirements']: length-17 sequence; area a uses position a-1"},"variables":{"selected[t]":"Binary for each team t"},"constraints":["For each area a: sum(selected[t] for t in coverage[a]) >= area_requirements[a-1]"],"objective":"Minimize sum(team_costs[t-1] * selected[t] for t in teams)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    team_costs = params["team_costs"]
    area_requirements = params["area_requirements"]

    if len(team_costs) != 13:
        return {"objective": None, "status": "invalid_team_costs"}
    if len(area_requirements) != 17:
        return {"objective": None, "status": "invalid_area_requirements"}

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

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "infeasible_or_solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}