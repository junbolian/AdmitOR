# IR: {"sets":{"teams":"1..15","tasks":"1..16","coverage":{"1":[4,5,7,8,10,12,13,14],"2":[2,3,7,9,10,13,14],"3":[3,5,6,7,11,12],"4":[1,2,4,6,8,9,10,13],"5":[2,4,6,7,8,10,13,15],"6":[3,7,8,10,11,15],"7":[1,3,9,10,12,14],"8":[5,6,8,14,15],"9":[1,2,9,10,14],"10":[3,7,11,12,13],"11":[1,4,8,11,12,13,14,15],"12":[2,5,15],"13":[2,4,9,11,13,15],"14":[3,8,9,11,12,15],"15":[3,6,7,9,12,15],"16":[10,13,15]}},"params":{"team_costs":"15-element zero-based sequence from params[\"team_costs\"]","task_requirements":"16-element zero-based sequence from params[\"task_requirements\"]"},"decision_variables":{"selected[team]":"Binary"},"constraints":["For each task: sum(selected[team] for team in coverage[task]) >= task_requirements[task-1]"],"objective":"minimize sum(team_costs[team-1] * selected[team] for team in teams)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve using zero-based cost and requirement sequences in params."""
    team_costs = params["team_costs"]
    task_requirements = params["task_requirements"]

    coverage = {
        1: (4, 5, 7, 8, 10, 12, 13, 14),
        2: (2, 3, 7, 9, 10, 13, 14),
        3: (3, 5, 6, 7, 11, 12),
        4: (1, 2, 4, 6, 8, 9, 10, 13),
        5: (2, 4, 6, 7, 8, 10, 13, 15),
        6: (3, 7, 8, 10, 11, 15),
        7: (1, 3, 9, 10, 12, 14),
        8: (5, 6, 8, 14, 15),
        9: (1, 2, 9, 10, 14),
        10: (3, 7, 11, 12, 13),
        11: (1, 4, 8, 11, 12, 13, 14, 15),
        12: (2, 5, 15),
        13: (2, 4, 9, 11, 13, 15),
        14: (3, 8, 9, 11, 12, 15),
        15: (3, 6, 7, 9, 12, 15),
        16: (10, 13, 15),
    }

    model = pyo.ConcreteModel()
    model.teams = pyo.RangeSet(1, 15)
    model.tasks = pyo.RangeSet(1, 16)

    model.team_cost = pyo.Param(
        model.teams,
        initialize={
            team: team_costs[team - 1]
            for team in model.teams
        },
        within=pyo.Reals,
    )
    model.task_requirement = pyo.Param(
        model.tasks,
        initialize={
            task: task_requirements[task - 1]
            for task in model.tasks
        },
        within=pyo.Reals,
    )
    model.selected = pyo.Var(model.teams, domain=pyo.Binary)

    def coverage_rule(problem, task):
        return (
            sum(problem.selected[team] for team in coverage[task])
            >= problem.task_requirement[task]
        )

    model.coverage_constraints = pyo.Constraint(
        model.tasks,
        rule=coverage_rule,
    )
    model.total_cost = pyo.Objective(
        expr=sum(
            model.team_cost[team] * model.selected[team]
            for team in model.teams
        ),
        sense=pyo.minimize,
    )

    # HiGHS raises RuntimeError when no feasible solution can be loaded.
    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "infeasible_or_failed"}

    # Success is determined solely by retrieving the objective value.
    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}