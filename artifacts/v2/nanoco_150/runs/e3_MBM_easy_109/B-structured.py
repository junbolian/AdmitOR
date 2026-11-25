# IR: {"sets":{"tasks":[0,1,2,3,4,5,6],"servers":[0,1,2,3,4],"paths":[[0,3],[0,4],[1,0],[1,3],[1,4],[2,0],[2,3],[3,1],[3,2],[4,0],[4,1],[5,2],[6,0],[6,3],[6,4]]},"params":{},"variables":{"x[task,server]":{"domain":"Binary","indices":"paths"}},"constraints":{"task_capacity":"For each task: sum(x[task,server] over compatible servers) <= 1","server_capacity":"For each server: sum(x[task,server] over compatible tasks) <= 1"},"objective":{"sense":"maximize","expression":"sum(x[task,server] over paths)"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Find a maximum-cardinality matching; no input parameters are required."""
    model = pyo.ConcreteModel()

    model.tasks = pyo.Set(initialize=range(7), ordered=True)
    model.servers = pyo.Set(initialize=range(5), ordered=True)
    model.paths = pyo.Set(
        dimen=2,
        initialize=[
            (0, 3), (0, 4),
            (1, 0), (1, 3), (1, 4),
            (2, 0), (2, 3),
            (3, 1), (3, 2),
            (4, 0), (4, 1),
            (5, 2),
            (6, 0), (6, 3), (6, 4),
        ],
        ordered=True,
    )

    model.x = pyo.Var(model.paths, domain=pyo.Binary)

    def task_capacity_rule(instance, task):
        return sum(
            instance.x[task, server]
            for server in instance.servers
            if (task, server) in instance.paths
        ) <= 1

    def server_capacity_rule(instance, server):
        return sum(
            instance.x[task, server]
            for task in instance.tasks
            if (task, server) in instance.paths
        ) <= 1

    model.task_capacity = pyo.Constraint(
        model.tasks, rule=task_capacity_rule
    )
    model.server_capacity = pyo.Constraint(
        model.servers, rule=server_capacity_rule
    )

    model.total_assignments = pyo.Objective(
        expr=sum(model.x[task, server] for task, server in model.paths),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_assignments))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}