# IR: {"sets":{"teams":[1,2,3,4,5,6,7,8,9,10,11,12],"locations":[1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18],"coverage":{"1":[4,8,10,11],"2":[2,3,7,8,10],"3":[1,4,6],"4":[8,10,12],"5":[1,3,4,8,11],"6":[1,2,6,7,8,12],"7":[1,2,4,6,9,11],"8":[2,7,8,11],"9":[2,3,4,6],"10":[2,3,5,6,9,10,11,12],"11":[2,3,4,10],"12":[4,5,9,10,11],"13":[7,9,12],"14":[1,7,9,11],"15":[6,7,8,9,10],"16":[1,4,6,7,9,10,12],"17":[4,5,7,8,10,12],"18":[1,5,8,9]}},"params":{"deployment_costs":"input sequence of length 12; team t uses params['deployment_costs'][t-1]","coverage_requirements":"input sequence of length 18; location l uses params['coverage_requirements'][l-1]"},"decision_variables":{"deployed[t]":"binary for each team t"},"constraints":["For each location l: sum(deployed[t] for t in coverage[l]) >= coverage_requirements[l-1]"],"objective":"minimize sum(deployment_costs[t-1] * deployed[t] for t in teams)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve using input sequences ordered by team and location number."""
    deployment_costs = params["deployment_costs"]
    coverage_requirements = params["coverage_requirements"]

    if len(deployment_costs) != 12:
        raise ValueError("deployment_costs must contain exactly 12 entries.")
    if len(coverage_requirements) != 18:
        raise ValueError("coverage_requirements must contain exactly 18 entries.")

    coverage = {
        1: (4, 8, 10, 11),
        2: (2, 3, 7, 8, 10),
        3: (1, 4, 6),
        4: (8, 10, 12),
        5: (1, 3, 4, 8, 11),
        6: (1, 2, 6, 7, 8, 12),
        7: (1, 2, 4, 6, 9, 11),
        8: (2, 7, 8, 11),
        9: (2, 3, 4, 6),
        10: (2, 3, 5, 6, 9, 10, 11, 12),
        11: (2, 3, 4, 10),
        12: (4, 5, 9, 10, 11),
        13: (7, 9, 12),
        14: (1, 7, 9, 11),
        15: (6, 7, 8, 9, 10),
        16: (1, 4, 6, 7, 9, 10, 12),
        17: (4, 5, 7, 8, 10, 12),
        18: (1, 5, 8, 9),
    }

    model = pyo.ConcreteModel()
    model.teams = pyo.RangeSet(1, 12)
    model.locations = pyo.RangeSet(1, 18)

    model.deployment_cost = pyo.Param(
        model.teams,
        initialize={
            team: deployment_costs[team - 1]
            for team in model.teams
        },
        within=pyo.Reals,
    )
    model.coverage_requirement = pyo.Param(
        model.locations,
        initialize={
            location: coverage_requirements[location - 1]
            for location in model.locations
        },
        within=pyo.Reals,
    )

    model.deployed = pyo.Var(model.teams, domain=pyo.Binary)

    def coverage_rule(block, location):
        return (
            sum(block.deployed[team] for team in coverage[location])
            >= block.coverage_requirement[location]
        )

    model.coverage_constraints = pyo.Constraint(
        model.locations,
        rule=coverage_rule,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.deployment_cost[team] * model.deployed[team]
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