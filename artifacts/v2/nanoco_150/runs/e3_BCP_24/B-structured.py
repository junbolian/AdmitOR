# IR: {"sets":{"V":"0..7","E":[[0,1],[0,2],[0,3],[0,5],[0,6],[0,7],[1,7],[2,4],[2,6],[2,7],[3,6],[4,6],[4,7],[5,7]]},"params":{"turnaround":"14 finite nonnegative values from params['turnaround'], in E order","gap[k]":"ceil(turnaround[k]); equivalent for integer start times","H":"7*max(gap[k]); valid horizon from sequentially spacing all 8 procedures","M[k]":"H+gap[k]"},"variables":{"start[i]":"integer in [0,H]","order[k]":"binary","makespan":"integer in [0,H]"},"constraints":["start[u]-start[v]>=gap[k]-M[k]*(1-order[k]) for k,(u,v) in E","start[v]-start[u]>=gap[k]-M[k]*order[k] for k,(u,v) in E","makespan>=start[i] for i in V"],"objective":"minimize makespan"}

import math

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    edges = (
        (0, 1),
        (0, 2),
        (0, 3),
        (0, 5),
        (0, 6),
        (0, 7),
        (1, 7),
        (2, 4),
        (2, 6),
        (2, 7),
        (3, 6),
        (4, 6),
        (4, 7),
        (5, 7),
    )

    turnaround = list(params["turnaround"])
    if len(turnaround) != len(edges):
        return {"objective": None, "status": "invalid_turnaround_length"}

    turnaround = [float(value) for value in turnaround]
    if any(not math.isfinite(value) or value < 0 for value in turnaround):
        return {"objective": None, "status": "invalid_turnaround"}

    gaps = [math.ceil(value) for value in turnaround]
    horizon = (8 - 1) * max(gaps)

    model = pyo.ConcreteModel()
    model.procedures = pyo.RangeSet(0, 7)
    model.dependencies = pyo.RangeSet(0, len(edges) - 1)

    model.gap = pyo.Param(
        model.dependencies,
        initialize={k: gaps[k] for k in range(len(edges))},
        within=pyo.NonNegativeIntegers,
    )
    model.big_m = pyo.Param(
        model.dependencies,
        initialize={k: horizon + gaps[k] for k in range(len(edges))},
        within=pyo.NonNegativeIntegers,
    )

    model.start = pyo.Var(
        model.procedures,
        domain=pyo.NonNegativeIntegers,
        bounds=(0, horizon),
    )
    model.order = pyo.Var(model.dependencies, domain=pyo.Binary)
    model.makespan = pyo.Var(
        domain=pyo.NonNegativeIntegers,
        bounds=(0, horizon),
    )

    def separation_forward_rule(instance, k):
        u, v = edges[k]
        return (
            instance.start[u] - instance.start[v]
            >= instance.gap[k]
            - instance.big_m[k] * (1 - instance.order[k])
        )

    def separation_reverse_rule(instance, k):
        u, v = edges[k]
        return (
            instance.start[v] - instance.start[u]
            >= instance.gap[k] - instance.big_m[k] * instance.order[k]
        )

    def makespan_rule(instance, i):
        return instance.makespan >= instance.start[i]

    model.separation_forward = pyo.Constraint(
        model.dependencies, rule=separation_forward_rule
    )
    model.separation_reverse = pyo.Constraint(
        model.dependencies, rule=separation_reverse_rule
    )
    model.makespan_bounds = pyo.Constraint(
        model.procedures, rule=makespan_rule
    )
    model.total_makespan = pyo.Objective(
        expr=model.makespan,
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPsi HiGHS raises this when it cannot load a feasible solution.
        # Unrelated runtime errors remain visible to the calling harness.
        if "a feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_makespan))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}