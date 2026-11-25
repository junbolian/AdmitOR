import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    team_costs = params["team_costs"]
    task_requirements = params["task_requirements"]
    num_teams = params["num_teams"]
    num_tasks = params["num_tasks"]

    # Coverage: for each task index t (0-based), list of team indices (0-based) capable of covering it
    coverage = {
        0: [3, 4, 6, 7, 9, 11, 12, 13],
        1: [1, 2, 6, 8, 9, 12, 13],
        2: [2, 4, 5, 6, 10, 11],
        3: [0, 1, 3, 5, 7, 8, 9, 12],
        4: [1, 3, 5, 6, 7, 9, 12, 14],
        5: [2, 6, 7, 9, 10, 14],
        6: [0, 2, 8, 9, 11, 13],
        7: [4, 5, 7, 13, 14],
        8: [0, 1, 8, 9, 13],
        9: [2, 6, 10, 11, 12],
        10: [0, 3, 7, 10, 11, 12, 13, 14],
        11: [1, 4, 14],
        12: [1, 3, 8, 10, 12, 14],
        13: [2, 7, 8, 10, 11, 14],
        14: [2, 5, 6, 8, 11, 14],
        15: [9, 12, 14],
    }

    model = pyo.ConcreteModel()

    model.TEAMS = pyo.RangeSet(0, num_teams - 1)
    model.TASKS = pyo.RangeSet(0, num_tasks - 1)

    model.select = pyo.Var(model.TEAMS, domain=pyo.Binary)

    def cost_rule(m):
        return sum(team_costs[i] * m.select[i] for i in m.TEAMS)

    model.total_cost = pyo.Objective(rule=cost_rule, sense=pyo.minimize)

    def cover_rule(m, t):
        return sum(m.select[i] for i in coverage[t]) >= task_requirements[t]

    model.coverage = pyo.Constraint(model.TASKS, rule=cover_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}