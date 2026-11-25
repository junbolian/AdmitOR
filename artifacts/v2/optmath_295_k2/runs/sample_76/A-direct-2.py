import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    team_costs = params["team_costs"]
    task_requirements = params["task_requirements"]

    # Structural data: which teams can cover which tasks (1-indexed teams and tasks)
    cover = {
        1: [4, 5, 7, 8, 10, 12, 13, 14],
        2: [2, 3, 7, 9, 10, 13, 14],
        3: [3, 5, 6, 7, 11, 12],
        4: [1, 2, 4, 6, 8, 9, 10, 13],
        5: [2, 4, 6, 7, 8, 10, 13, 15],
        6: [3, 7, 8, 10, 11, 15],
        7: [1, 3, 9, 10, 12, 14],
        8: [5, 6, 8, 14, 15],
        9: [1, 2, 9, 10, 14],
        10: [3, 7, 11, 12, 13],
        11: [1, 4, 8, 11, 12, 13, 14, 15],
        12: [2, 5, 15],
        13: [2, 4, 9, 11, 13, 15],
        14: [3, 8, 9, 11, 12, 15],
        15: [3, 6, 7, 9, 12, 15],
        16: [10, 13, 15],
    }

    n_teams = 15
    n_tasks = 16

    model = pyo.ConcreteModel()

    model.TEAMS = pyo.RangeSet(1, n_teams)
    model.TASKS = pyo.RangeSet(1, n_tasks)

    model.x = pyo.Var(model.TEAMS, domain=pyo.Binary)

    def obj_rule(m):
        return sum(team_costs[i - 1] * m.x[i] for i in m.TEAMS)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def cover_rule(m, j):
        return sum(m.x[i] for i in cover[j]) >= task_requirements[j - 1]

    model.coverage = pyo.Constraint(model.TASKS, rule=cover_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}