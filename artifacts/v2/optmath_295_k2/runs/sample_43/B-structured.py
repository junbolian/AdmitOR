# IR: {"sets":{"W":"1..10","T":"1..22","E[t]":"fixed eligible-worker sets specified in eligibility"},"params":{"worker_costs":"input cost indexed by W"},"variables":{"selected[w]":"binary, w in W"},"constraints":["For each t in T: sum(selected[w] for w in E[t]) >= 1"],"objective":"minimize sum(worker_costs[w] * selected[w] for w in W)"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    worker_costs = params["worker_costs"]

    eligibility = {
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

    # Accept worker-indexed mappings (integer or JSON string keys), or
    # a sequence whose entries are ordered from worker 1 through worker 10.
    if isinstance(worker_costs, Mapping):
        costs = {
            worker: worker_costs[worker]
            if worker in worker_costs
            else worker_costs[str(worker)]
            for worker in range(1, 11)
        }
    else:
        costs = {
            worker: worker_costs[worker - 1]
            for worker in range(1, 11)
        }

    model = pyo.ConcreteModel()
    model.workers = pyo.RangeSet(1, 10)
    model.tasks = pyo.RangeSet(1, 22)
    model.worker_cost = pyo.Param(
        model.workers,
        initialize=costs,
        within=pyo.Reals,
    )
    model.selected = pyo.Var(model.workers, domain=pyo.Binary)

    def coverage_rule(instance, task):
        return sum(
            instance.selected[worker]
            for worker in eligibility[task]
        ) >= 1

    model.task_coverage = pyo.Constraint(
        model.tasks,
        rule=coverage_rule,
    )
    model.total_cost = pyo.Objective(
        expr=sum(
            model.worker_cost[worker] * model.selected[worker]
            for worker in model.workers
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPsi raises this when it cannot load a feasible solution.
        # Continue to the objective retrieval check; propagate other errors.
        if "A feasible solution was not found" not in str(exc):
            raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}