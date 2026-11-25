import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    team_costs = params["team_costs"]
    task_requirements = params["task_requirements"]

    num_teams = len(team_costs)
    num_tasks = len(task_requirements)

    # coverage[t] = list of team indices (0-based) capable of covering task t
    coverage = [
        [3, 4, 6, 7, 9, 11, 12, 13],
        [1, 2, 6, 8, 9, 12, 13],
        [2, 4, 5, 6, 10, 11],
        [0, 1, 3, 5, 7, 8, 9, 12],
        [1, 3, 5, 6, 7, 9, 12, 14],
        [2, 6, 7, 9, 10, 14],
        [0, 2, 8, 9, 11, 13],
        [4, 5, 7, 13, 14],
        [0, 1, 8, 9, 13],
        [2, 6, 10, 11, 12],
        [0, 3, 7, 10, 11, 12, 13, 14],
        [1, 4, 14],
        [1, 3, 8, 10, 12, 14],
        [2, 7, 8, 10, 11, 14],
        [2, 5, 6, 8, 11, 14],
        [9, 12, 14],
    ]

    model = pyo.ConcreteModel()

    model.TEAMS = pyo.RangeSet(0, num_teams - 1)
    model.TASKS = pyo.RangeSet(0, num_tasks - 1)

    model.x = pyo.Var(model.TEAMS, domain=pyo.Binary)

    model.obj = pyo.Objective(
        expr=sum(team_costs[i] * model.x[i] for i in model.TEAMS),
        sense=pyo.minimize,
    )

    def task_rule(m, t):
        return sum(m.x[i] for i in coverage[t]) >= task_requirements[t]

    model.task_coverage = pyo.Constraint(model.TASKS, rule=task_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}