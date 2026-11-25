# IR: {"sets":{"machinists":"0..5","jobs":"0..5"},"params":{"cost_matrix":"nonnegative machining durations indexed by machinist and job, read from params['cost_matrix']"},"variables":{"assigned[i,j]":"binary","bottleneck":"nonnegative continuous"},"constraints":["For each machinist i: sum_j assigned[i,j] = 1.","For each job j: sum_i assigned[i,j] = 1.","For each pair (i,j): bottleneck >= cost_matrix[i,j] * assigned[i,j]."],"objective":"Minimize bottleneck."}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost_matrix = params["cost_matrix"]

    model = pyo.ConcreteModel()
    model.machinists = pyo.RangeSet(0, 5)
    model.jobs = pyo.RangeSet(0, 5)

    model.machining_time = pyo.Param(
        model.machinists,
        model.jobs,
        initialize=lambda mdl, i, j: cost_matrix[i][j],
        within=pyo.NonNegativeReals,
    )

    model.assigned = pyo.Var(
        model.machinists,
        model.jobs,
        domain=pyo.Binary,
    )
    model.bottleneck = pyo.Var(domain=pyo.NonNegativeReals)

    model.machinist_assignment = pyo.Constraint(
        model.machinists,
        rule=lambda mdl, i: sum(
            mdl.assigned[i, j] for j in mdl.jobs
        ) == 1,
    )

    model.job_assignment = pyo.Constraint(
        model.jobs,
        rule=lambda mdl, j: sum(
            mdl.assigned[i, j] for i in mdl.machinists
        ) == 1,
    )

    model.bottleneck_bound = pyo.Constraint(
        model.machinists,
        model.jobs,
        rule=lambda mdl, i, j: (
            mdl.bottleneck
            >= mdl.machining_time[i, j] * mdl.assigned[i, j]
        ),
    )

    model.objective = pyo.Objective(
        expr=model.bottleneck,
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.objective))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}