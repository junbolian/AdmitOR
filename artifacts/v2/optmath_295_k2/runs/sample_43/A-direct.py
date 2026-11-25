import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    worker_costs = params["worker_costs"]

    num_workers = 10
    num_tasks = 22

    # Task -> list of capable workers (1-indexed worker ids)
    capable = {
        1: [1, 2, 3, 4, 6, 9, 10],
        2: [5, 6, 8, 9, 10],
        3: [3, 4, 5, 10],
        4: [3, 5, 6],
        5: [3, 5, 7, 9, 10],
        6: [2, 4, 6, 10],
        7: [1, 3, 4, 5, 7, 8, 9],
        8: [2, 3, 4, 5, 7, 8],
        9: [1, 3, 5, 6, 7],
        10: [1, 4, 5, 6, 9, 10],
        11: [2, 4, 5, 7, 10],
        12: [4, 5, 8, 10],
        13: [2, 3, 7, 9],
        14: [2, 4, 5, 6, 8, 9],
        15: [3, 4, 5, 6, 7, 9],
        16: [3, 4, 6, 7, 9, 10],
        17: [1, 3, 4, 5, 7],
        18: [2, 4, 5, 6, 10],
        19: [1, 6, 7, 9],
        20: [3, 6, 7, 9, 10],
        21: [4, 5, 6],
        22: [1, 3, 4, 5, 8, 9],
    }

    model = pyo.ConcreteModel()

    model.WORKERS = pyo.Set(initialize=list(range(1, num_workers + 1)))
    model.TASKS = pyo.Set(initialize=list(range(1, num_tasks + 1)))

    model.x = pyo.Var(model.WORKERS, domain=pyo.Binary)

    def cost_rule(m):
        return sum(worker_costs[w - 1] * m.x[w] for w in m.WORKERS)

    model.total_cost = pyo.Objective(rule=cost_rule, sense=pyo.minimize)

    def task_rule(m, t):
        return sum(m.x[w] for w in capable[t]) >= 1

    model.task_cover = pyo.Constraint(model.TASKS, rule=task_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}