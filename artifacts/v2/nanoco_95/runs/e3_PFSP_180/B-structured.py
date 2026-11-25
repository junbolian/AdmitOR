# IR: {"sets":{"jobs":[0,1,2,3],"positions":[0,1,2,3],"machines":[0,1,2]},"params":{"p":"params['p'][job][machine], nonnegative processing times"},"variables":{"x[job,position]":"binary; assigns a job to a common position on every machine","completion[position,machine]":"nonnegative continuous"},"constraints":["Each job occupies exactly one position.","Each position contains exactly one job.","completion[k,h] >= sum_j p[j,h]*x[j,k] + (completion[k,h-1] if h>0 else 0).","For k>0: completion[k,h] >= completion[k-1,h] + sum_j p[j,h]*x[j,k]."],"objective":"Minimize completion[3,2]."}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.jobs = pyo.RangeSet(0, 3)
    model.positions = pyo.RangeSet(0, 3)
    model.machines = pyo.RangeSet(0, 2)

    model.processing_time = pyo.Param(
        model.jobs,
        model.machines,
        initialize=lambda mdl, job, machine: params["p"][job][machine],
        within=pyo.NonNegativeReals,
    )

    model.x = pyo.Var(
        model.jobs,
        model.positions,
        domain=pyo.Binary,
    )
    model.completion = pyo.Var(
        model.positions,
        model.machines,
        domain=pyo.NonNegativeReals,
    )

    def job_assignment_rule(mdl, job):
        return sum(mdl.x[job, position] for position in mdl.positions) == 1

    model.job_assignment = pyo.Constraint(
        model.jobs,
        rule=job_assignment_rule,
    )

    def position_assignment_rule(mdl, position):
        return sum(mdl.x[job, position] for job in mdl.jobs) == 1

    model.position_assignment = pyo.Constraint(
        model.positions,
        rule=position_assignment_rule,
    )

    model.position_duration = pyo.Expression(
        model.positions,
        model.machines,
        rule=lambda mdl, position, machine: sum(
            mdl.processing_time[job, machine] * mdl.x[job, position]
            for job in mdl.jobs
        ),
    )

    def route_precedence_rule(mdl, position, machine):
        previous_completion = (
            mdl.completion[position, machine - 1] if machine > 0 else 0
        )
        return mdl.completion[position, machine] >= (
            previous_completion + mdl.position_duration[position, machine]
        )

    model.route_precedence = pyo.Constraint(
        model.positions,
        model.machines,
        rule=route_precedence_rule,
    )

    def machine_sequence_rule(mdl, position, machine):
        if position == 0:
            return pyo.Constraint.Skip
        return mdl.completion[position, machine] >= (
            mdl.completion[position - 1, machine]
            + mdl.position_duration[position, machine]
        )

    model.machine_sequence = pyo.Constraint(
        model.positions,
        model.machines,
        rule=machine_sequence_rule,
    )

    model.makespan_objective = pyo.Objective(
        expr=model.completion[3, 2],
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "a feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.makespan_objective))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}