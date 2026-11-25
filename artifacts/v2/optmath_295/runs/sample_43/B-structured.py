# IR: {"sets":{"workers":"1..10","tasks":"1..22","eligible":{"1":[1,2,3,4,6,9,10],"2":[5,6,8,9,10],"3":[3,4,5,10],"4":[3,5,6],"5":[3,5,7,9,10],"6":[2,4,6,10],"7":[1,3,4,5,7,8,9],"8":[2,3,4,5,7,8],"9":[1,3,5,6,7],"10":[1,4,5,6,9,10],"11":[2,4,5,7,10],"12":[4,5,8,10],"13":[2,3,7,9],"14":[2,4,5,6,8,9],"15":[3,4,5,6,7,9],"16":[3,4,6,7,9,10],"17":[1,3,4,5,7],"18":[2,4,5,6,10],"19":[1,6,7,9],"20":[3,6,7,9,10],"21":[4,5,6],"22":[1,3,4,5,8,9]}},"params":{"worker_cost_1":"real","worker_cost_2":"real","worker_cost_3":"real","worker_cost_4":"real","worker_cost_5":"real","worker_cost_6":"real","worker_cost_7":"real","worker_cost_8":"real","worker_cost_9":"real","worker_cost_10":"real"},"variables":{"selected[w]":"binary for each worker w"},"constraints":["coverage[t]: sum(selected[w] for w in eligible[t]) >= 1 for each task t"],"objective":"minimize sum(worker_cost_w * selected[w] for w in workers)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    worker_costs = {
        1: params["worker_cost_1"],
        2: params["worker_cost_2"],
        3: params["worker_cost_3"],
        4: params["worker_cost_4"],
        5: params["worker_cost_5"],
        6: params["worker_cost_6"],
        7: params["worker_cost_7"],
        8: params["worker_cost_8"],
        9: params["worker_cost_9"],
        10: params["worker_cost_10"],
    }

    eligible_workers = {
        1: (1, 2, 3, 4, 6, 9, 10),
        2: (5, 6, 8, 9, 10),
        3: (3, 4, 5, 10),
        4: (3, 5, 6),
        5: (3, 5, 7, 9, 10),
        6: (2, 4, 6, 10),
        7: (1, 3, 4, 5, 7, 8, 9),
        8: (2, 3, 4, 5, 7, 8),
        9: (1, 3, 5, 6, 7),
        10: (1, 4, 5, 6, 9, 10),
        11: (2, 4, 5, 7, 10),
        12: (4, 5, 8, 10),
        13: (2, 3, 7, 9),
        14: (2, 4, 5, 6, 8, 9),
        15: (3, 4, 5, 6, 7, 9),
        16: (3, 4, 6, 7, 9, 10),
        17: (1, 3, 4, 5, 7),
        18: (2, 4, 5, 6, 10),
        19: (1, 6, 7, 9),
        20: (3, 6, 7, 9, 10),
        21: (4, 5, 6),
        22: (1, 3, 4, 5, 8, 9),
    }

    model = pyo.ConcreteModel()
    model.workers = pyo.RangeSet(1, 10)
    model.tasks = pyo.RangeSet(1, 22)
    model.worker_cost = pyo.Param(
        model.workers,
        initialize=worker_costs,
        within=pyo.Reals,
    )
    model.selected = pyo.Var(model.workers, domain=pyo.Binary)

    def coverage_rule(model, task):
        return sum(
            model.selected[worker] for worker in eligible_workers[task]
        ) >= 1

    model.coverage = pyo.Constraint(model.tasks, rule=coverage_rule)
    model.total_cost = pyo.Objective(
        expr=sum(
            model.worker_cost[worker] * model.selected[worker]
            for worker in model.workers
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}