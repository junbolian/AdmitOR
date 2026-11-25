# IR: {"sets":{"I":"range(params['num_workers'])","J":"range(params['num_tasks'])"},"params":{"cost_matrix":"params['cost_matrix'], indexed by I x J","num_workers":"params['num_workers']","num_tasks":"params['num_tasks']"},"variables":{"assignment[i,j]":"Binary for (i,j) in I x J","worst_latency":"NonNegativeReals"},"constraints":["For each i in I: sum(assignment[i,j] for j in J) == 1","For each j in J: sum(assignment[i,j] for i in I) == 1","For each i in I: worst_latency >= sum(cost_matrix[i][j] * assignment[i,j] for j in J)"],"objective":"Minimize worst_latency"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_workers = params["num_workers"]
    num_tasks = params["num_tasks"]
    cost_matrix = params["cost_matrix"]

    model = pyo.ConcreteModel()

    model.workers = pyo.Set(initialize=range(num_workers), ordered=True)
    model.tasks = pyo.Set(initialize=range(num_tasks), ordered=True)

    model.latency = pyo.Param(
        model.workers,
        model.tasks,
        initialize={
            (i, j): cost_matrix[i][j]
            for i in range(num_workers)
            for j in range(num_tasks)
        },
        within=pyo.NonNegativeReals,
    )

    model.assignment = pyo.Var(
        model.workers,
        model.tasks,
        domain=pyo.Binary,
    )
    model.worst_latency = pyo.Var(domain=pyo.NonNegativeReals)

    def server_assignment_rule(instance, i):
        return sum(
            instance.assignment[i, j] for j in instance.tasks
        ) == 1

    model.server_assignment = pyo.Constraint(
        model.workers,
        rule=server_assignment_rule,
    )

    def feed_assignment_rule(instance, j):
        return sum(
            instance.assignment[i, j] for i in instance.workers
        ) == 1

    model.feed_assignment = pyo.Constraint(
        model.tasks,
        rule=feed_assignment_rule,
    )

    def bottleneck_rule(instance, i):
        return instance.worst_latency >= sum(
            instance.latency[i, j] * instance.assignment[i, j]
            for j in instance.tasks
        )

    model.bottleneck_bounds = pyo.Constraint(
        model.workers,
        rule=bottleneck_rule,
    )

    model.bottleneck_objective = pyo.Objective(
        expr=model.worst_latency,
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.bottleneck_objective))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}