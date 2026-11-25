# IR: {"sets":{"machines":[0,1,2,3,4],"jobs":[0,1,2,3,4]},"params":{"processing_time":{"source":"params['processing_time']","indices":["machines","jobs"],"domain":"NonNegativeReals"}},"variables":{"assigned":{"indices":["machines","jobs"],"type":"Binary"},"maximum_duration":{"type":"NonNegativeReals"}},"constraints":["For each machine i: sum(assigned[i,j] for j in jobs) == 1","For each job j: sum(assigned[i,j] for i in machines) == 1","For each machine i and job j: maximum_duration >= processing_time[i,j] * assigned[i,j]"],"objective":{"sense":"minimize","expression":"maximum_duration"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    processing_time = params["processing_time"]

    model = pyo.ConcreteModel()

    model.machines = pyo.RangeSet(0, 4)
    model.jobs = pyo.RangeSet(0, 4)

    model.processing_time = pyo.Param(
        model.machines,
        model.jobs,
        initialize=lambda mdl, machine_idx, job_idx: processing_time[machine_idx][job_idx],
        within=pyo.NonNegativeReals,
    )

    model.assigned = pyo.Var(
        model.machines,
        model.jobs,
        domain=pyo.Binary,
    )
    model.maximum_duration = pyo.Var(domain=pyo.NonNegativeReals)

    def machine_assignment_rule(mdl, machine_idx):
        return sum(
            mdl.assigned[machine_idx, job_idx] for job_idx in mdl.jobs
        ) == 1

    model.machine_assignment = pyo.Constraint(
        model.machines,
        rule=machine_assignment_rule,
    )

    def job_assignment_rule(mdl, job_idx):
        return sum(
            mdl.assigned[machine_idx, job_idx] for machine_idx in mdl.machines
        ) == 1

    model.job_assignment = pyo.Constraint(
        model.jobs,
        rule=job_assignment_rule,
    )

    def bottleneck_rule(mdl, machine_idx, job_idx):
        return mdl.maximum_duration >= (
            mdl.processing_time[machine_idx, job_idx]
            * mdl.assigned[machine_idx, job_idx]
        )

    model.bottleneck_bound = pyo.Constraint(
        model.machines,
        model.jobs,
        rule=bottleneck_rule,
    )

    model.objective = pyo.Objective(
        expr=model.maximum_duration,
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "infeasible_or_failed"}

    try:
        obj_val = float(pyo.value(model.objective))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}