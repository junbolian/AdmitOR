# IR: {"sets":{"J":["J0","J1","J2"],"M":["M0","M1","M2"],"O":"J x M","C":"unordered pairs (a,b) of distinct operations sharing a lot or tool"},"params":{"p[J0,M0]":"processing_time_J0_M0","p[J0,M1]":"processing_time_J0_M1","p[J0,M2]":"processing_time_J0_M2","p[J1,M0]":"processing_time_J1_M0","p[J1,M1]":"processing_time_J1_M1","p[J1,M2]":"processing_time_J1_M2","p[J2,M0]":"processing_time_J2_M0","p[J2,M1]":"processing_time_J2_M1","p[J2,M2]":"processing_time_J2_M2","H":"sum(p[o] for o in O); p[o]>=0"},"variables":{"s[o]":"continuous, 0<=s[o]<=H-p[o]","y[a,b]":"binary for (a,b) in C","Cmax":"continuous, 0<=Cmax<=H"},"constraints":["s[a]+p[a]<=s[b]+H*(1-y[a,b]) for (a,b) in C","s[b]+p[b]<=s[a]+H*y[a,b] for (a,b) in C","Cmax>=s[o]+p[o] for o in O"],"objective":"minimize Cmax"}
from itertools import combinations

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    processing_times = {
        ("J0", "M0"): params["processing_time_J0_M0"],
        ("J0", "M1"): params["processing_time_J0_M1"],
        ("J0", "M2"): params["processing_time_J0_M2"],
        ("J1", "M0"): params["processing_time_J1_M0"],
        ("J1", "M1"): params["processing_time_J1_M1"],
        ("J1", "M2"): params["processing_time_J1_M2"],
        ("J2", "M0"): params["processing_time_J2_M0"],
        ("J2", "M1"): params["processing_time_J2_M1"],
        ("J2", "M2"): params["processing_time_J2_M2"],
    }

    model = pyo.ConcreteModel()
    model.J = pyo.Set(initialize=["J0", "J1", "J2"], ordered=True)
    model.M = pyo.Set(initialize=["M0", "M1", "M2"], ordered=True)
    model.O = pyo.Set(
        dimen=2,
        initialize=[(job, tool) for job in model.J for tool in model.M],
        ordered=True,
    )
    model.p = pyo.Param(
        model.O,
        initialize=processing_times,
        within=pyo.NonNegativeReals,
    )

    horizon = sum(pyo.value(model.p[job, tool]) for job, tool in model.O)
    model.H = pyo.Param(initialize=horizon, within=pyo.NonNegativeReals)

    conflicts = [
        (job_a, tool_a, job_b, tool_b)
        for (job_a, tool_a), (job_b, tool_b) in combinations(model.O, 2)
        if job_a == job_b or tool_a == tool_b
    ]
    model.C = pyo.Set(dimen=4, initialize=conflicts, ordered=True)

    def start_bounds(instance, job, tool):
        return (0, pyo.value(instance.H - instance.p[job, tool]))

    model.s = pyo.Var(
        model.O,
        domain=pyo.NonNegativeReals,
        bounds=start_bounds,
    )
    model.y = pyo.Var(model.C, domain=pyo.Binary)
    model.Cmax = pyo.Var(
        domain=pyo.NonNegativeReals,
        bounds=(0, horizon),
    )

    def first_precedence(instance, job_a, tool_a, job_b, tool_b):
        return (
            instance.s[job_a, tool_a] + instance.p[job_a, tool_a]
            <= instance.s[job_b, tool_b]
            + instance.H * (1 - instance.y[job_a, tool_a, job_b, tool_b])
        )

    def second_precedence(instance, job_a, tool_a, job_b, tool_b):
        return (
            instance.s[job_b, tool_b] + instance.p[job_b, tool_b]
            <= instance.s[job_a, tool_a]
            + instance.H * instance.y[job_a, tool_a, job_b, tool_b]
        )

    def completion_bound(instance, job, tool):
        return instance.Cmax >= instance.s[job, tool] + instance.p[job, tool]

    model.first_precedence = pyo.Constraint(model.C, rule=first_precedence)
    model.second_precedence = pyo.Constraint(model.C, rule=second_precedence)
    model.completion_bound = pyo.Constraint(model.O, rule=completion_bound)
    model.makespan_objective = pyo.Objective(
        expr=model.Cmax,
        sense=pyo.minimize,
    )

    failure_reason = "objective_unavailable"
    try:
        Highs().solve(model)
    except RuntimeError:
        failure_reason = "solver_failed"

    try:
        obj_val = float(pyo.value(model.makespan_objective))
    except (ValueError, TypeError):
        return {"objective": None, "status": failure_reason}

    return {"objective": obj_val, "status": "optimal"}