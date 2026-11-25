# IR: {"sets":{"workers":"1..10","tasks":"1..22","eligible":{"1":[1,2,3,4,6,9,10],"2":[5,6,8,9,10],"3":[3,4,5,10],"4":[3,5,6],"5":[3,5,7,9,10],"6":[2,4,6,10],"7":[1,3,4,5,7,8,9],"8":[2,3,4,5,7,8],"9":[1,3,5,6,7],"10":[1,4,5,6,9,10],"11":[2,4,5,7,10],"12":[4,5,8,10],"13":[2,3,7,9],"14":[2,4,5,6,8,9],"15":[3,4,5,6,7,9],"16":[3,4,6,7,9,10],"17":[1,3,4,5,7],"18":[2,4,5,6,10],"19":[1,6,7,9],"20":[3,6,7,9,10],"21":[4,5,6],"22":[1,3,4,5,8,9]}},"params":{"worker_costs":"params['worker_costs']; mapping indexed 1..10 (integer or string keys), or sequence in worker order"},"variables":{"selected[worker]":"binary"},"constraints":["coverage[task]: sum(selected[worker] for worker in eligible[task]) >= 1"],"objective":"minimize sum(worker_costs[worker] * selected[worker] for worker in workers)"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    raw_costs = params["worker_costs"]

    if isinstance(raw_costs, Mapping):
        costs = {
            worker: (
                raw_costs[worker]
                if worker in raw_costs
                else raw_costs[str(worker)]
            )
            for worker in range(1, 11)
        }
    else:
        if len(raw_costs) != 10:
            raise ValueError("worker_costs must contain exactly 10 values.")
        costs = {
            worker: raw_costs[worker - 1]
            for worker in range(1, 11)
        }

    eligible = {
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
    model.eligible = pyo.Set(
        model.tasks,
        within=model.workers,
        initialize=eligible,
    )
    model.worker_costs = pyo.Param(
        model.workers,
        initialize=costs,
        within=pyo.Reals,
    )
    model.selected = pyo.Var(model.workers, domain=pyo.Binary)

    def coverage_rule(instance, task):
        return sum(
            instance.selected[worker]
            for worker in instance.eligible[task]
        ) >= 1

    model.coverage = pyo.Constraint(model.tasks, rule=coverage_rule)
    model.total_cost = pyo.Objective(
        expr=sum(
            model.worker_costs[worker] * model.selected[worker]
            for worker in model.workers
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