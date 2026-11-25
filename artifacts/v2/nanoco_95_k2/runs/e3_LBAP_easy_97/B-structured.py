# IR: {"sets":{"servers":"range(num_workers)","feeds":"range(num_tasks)"},"params":{"num_workers":"server cardinality","num_tasks":"feed cardinality","cost_matrix":"latency[server][feed]"},"variables":{"assigned[i,j]":"Binary","max_latency":"NonNegativeReals"},"constraints":["For each server i: sum_j assigned[i,j] = 1","For each feed j: sum_i assigned[i,j] = 1","For each (i,j): max_latency >= cost_matrix[i][j] * assigned[i,j]"],"objective":"minimize max_latency"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_workers = params["num_workers"]
    num_tasks = params["num_tasks"]
    cost_matrix = params["cost_matrix"]

    model = pyo.ConcreteModel()

    model.servers = pyo.Set(initialize=range(num_workers), ordered=True)
    model.feeds = pyo.Set(initialize=range(num_tasks), ordered=True)

    model.latency = pyo.Param(
        model.servers,
        model.feeds,
        initialize={
            (i, j): cost_matrix[i][j]
            for i in range(num_workers)
            for j in range(num_tasks)
        },
        within=pyo.NonNegativeReals,
    )

    model.assigned = pyo.Var(
        model.servers, model.feeds, domain=pyo.Binary
    )
    model.max_latency = pyo.Var(domain=pyo.NonNegativeReals)

    def server_assignment_rule(instance, i):
        return sum(
            instance.assigned[i, j] for j in instance.feeds
        ) == 1

    model.server_assignment = pyo.Constraint(
        model.servers, rule=server_assignment_rule
    )

    def feed_assignment_rule(instance, j):
        return sum(
            instance.assigned[i, j] for i in instance.servers
        ) == 1

    model.feed_assignment = pyo.Constraint(
        model.feeds, rule=feed_assignment_rule
    )

    def bottleneck_rule(instance, i, j):
        return (
            instance.max_latency
            >= instance.latency[i, j] * instance.assigned[i, j]
        )

    model.bottleneck_bound = pyo.Constraint(
        model.servers, model.feeds, rule=bottleneck_rule
    )

    model.objective = pyo.Objective(
        expr=model.max_latency, sense=pyo.minimize
    )

    solve_failed = False
    try:
        Highs().solve(model)
    except RuntimeError:
        solve_failed = True

    try:
        obj_val = float(pyo.value(model.objective))
    except ValueError:
        return {
            "objective": None,
            "status": "solve_failed" if solve_failed else "objective_unavailable",
        }

    return {"objective": obj_val, "status": "optimal"}