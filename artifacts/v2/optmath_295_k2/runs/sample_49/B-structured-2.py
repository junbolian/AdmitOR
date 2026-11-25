# IR: {"sets":{"teams":"1..14","locations":"1..21","coverage":{"1":[2,5,6,7,8,9,11,14],"2":[2,5,7,13],"3":[1,2,4,5,6,9,10,12,13],"4":[3,6,13,14],"5":[2,6,10],"6":[4,6,8,14],"7":[1,4,5,8,10,11,12,13,14],"8":[1,5,11,14],"9":[1,2,3,6,7,10,11,12],"10":[6,11,12,13],"11":[1,3,4,6,7,9],"12":[1,3,5,8,9],"13":[1,4,9,11,12,13,14],"14":[2,4,7,8,13],"15":[5,7,8,9],"16":[1,5,6,8,11,13],"17":[1,4,5,6,8,14],"18":[3,8,10,11,12,14],"19":[2,5,7,12,13],"20":[1,3,4,5,10,11,13],"21":[1,8,12,14]}},"params":{"team_costs":"length-14 sequence; team t uses params['team_costs'][t-1]","location_requirements":"length-21 sequence; location l uses params['location_requirements'][l-1]"},"decision_variables":{"selected[t]":"binary for each team t"},"constraints":["For each location l: sum(selected[t] for t in coverage[l]) >= location_requirements[l-1]"],"objective":"minimize sum(team_costs[t-1] * selected[t] for t in teams)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve the team deployment problem using zero-based parameter sequences."""
    team_costs = params["team_costs"]
    location_requirements = params["location_requirements"]

    if len(team_costs) != 14:
        raise ValueError("team_costs must contain exactly 14 entries.")
    if len(location_requirements) != 21:
        raise ValueError("location_requirements must contain exactly 21 entries.")

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

    model = pyo.ConcreteModel()
    model.teams = pyo.RangeSet(1, 14)
    model.locations = pyo.RangeSet(1, 21)

    model.deployment_cost = pyo.Param(
        model.teams,
        initialize={t: team_costs[t - 1] for t in model.teams},
        within=pyo.Reals,
    )
    model.required_coverage = pyo.Param(
        model.locations,
        initialize={
            loc: location_requirements[loc - 1] for loc in model.locations
        },
        within=pyo.Reals,
    )

    model.selected = pyo.Var(model.teams, domain=pyo.Binary)

    def coverage_rule(mdl, loc):
        return (
            pyo.quicksum(mdl.selected[t] for t in coverage[loc])
            >= mdl.required_coverage[loc]
        )

    model.coverage_constraints = pyo.Constraint(
        model.locations, rule=coverage_rule
    )
    model.total_cost = pyo.Objective(
        expr=pyo.quicksum(
            model.deployment_cost[t] * model.selected[t] for t in model.teams
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