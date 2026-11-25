# IR: {"sets":{"servers":[0,1,2,3,4],"feeds":[0,1,2,3,4]},"params":{"cost_matrix":"params['cost_matrix'], 5x5 real matrix"},"variables":{"assignment[i,j]":"Binary","max_latency":"Real"},"constraints":["For each server i: sum_j assignment[i,j] = 1","For each feed j: sum_i assignment[i,j] = 1","For each server i: max_latency >= sum_j cost_matrix[i,j]*assignment[i,j]"],"objective":"Minimize max_latency"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost_matrix = params["cost_matrix"]

    model = pyo.ConcreteModel()
    model.servers = pyo.RangeSet(0, 4)
    model.feeds = pyo.RangeSet(0, 4)

    model.latency = pyo.Param(
        model.servers,
        model.feeds,
        initialize=lambda mdl, i, j: cost_matrix[i][j],
        within=pyo.Reals,
    )

    model.assignment = pyo.Var(
        model.servers,
        model.feeds,
        domain=pyo.Binary,
    )
    model.max_latency = pyo.Var(domain=pyo.Reals)

    def server_assignment_rule(mdl, i):
        return sum(mdl.assignment[i, j] for j in mdl.feeds) == 1

    model.server_assignment = pyo.Constraint(
        model.servers,
        rule=server_assignment_rule,
    )

    def feed_assignment_rule(mdl, j):
        return sum(mdl.assignment[i, j] for i in mdl.servers) == 1

    model.feed_assignment = pyo.Constraint(
        model.feeds,
        rule=feed_assignment_rule,
    )

    def bottleneck_rule(mdl, i):
        return mdl.max_latency >= sum(
            mdl.latency[i, j] * mdl.assignment[i, j]
            for j in mdl.feeds
        )

    model.bottleneck_bounds = pyo.Constraint(
        model.servers,
        rule=bottleneck_rule,
    )

    model.objective = pyo.Objective(
        expr=model.max_latency,
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.objective))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}