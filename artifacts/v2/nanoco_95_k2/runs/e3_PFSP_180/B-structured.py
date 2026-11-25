# IR: {"sets":{"J":[0,1,2,3],"K":[0,1,2,3],"W":[0,1,2]},"params":{"p":"nonnegative processing times, params['p'][job][workstation]"},"variables":{"x[j,k]":"binary; job j occupies sequence position k","C[k,s]":"nonnegative continuous completion time at position k on workstation s"},"expressions":{"D[k,s]":"sum(p[j,s]*x[j,k] for j in J)"},"constraints":["sum(x[j,k] for k in K)=1 for each j","sum(x[j,k] for j in J)=1 for each k","C[0,0]=D[0,0]","C[k,s]>=D[k,s]+(C[k,s-1] if s>0 else 0) for each k,s","C[k,s]>=C[k-1,s]+D[k,s] for each k>0,s"],"objective":"minimize C[3,2]"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve the permutation flow-shop problem; p is indexed [job][workstation]."""
    processing_times = params["p"]

    model = pyo.ConcreteModel()

    model.jobs = pyo.RangeSet(0, 3)
    model.positions = pyo.RangeSet(0, 3)
    model.workstations = pyo.RangeSet(0, 2)

    model.processing_time = pyo.Param(
        model.jobs,
        model.workstations,
        initialize={
            (job, station): processing_times[job][station]
            for job in model.jobs
            for station in model.workstations
        },
        within=pyo.NonNegativeReals,
    )

    model.assignment = pyo.Var(
        model.jobs, model.positions, domain=pyo.Binary
    )
    model.completion = pyo.Var(
        model.positions, model.workstations, domain=pyo.NonNegativeReals
    )

    def duration_rule(mdl, position, station):
        return sum(
            mdl.processing_time[job, station] * mdl.assignment[job, position]
            for job in mdl.jobs
        )

    model.duration = pyo.Expression(
        model.positions, model.workstations, rule=duration_rule
    )

    def job_assignment_rule(mdl, job):
        return sum(
            mdl.assignment[job, position] for position in mdl.positions
        ) == 1

    model.job_assignment = pyo.Constraint(
        model.jobs, rule=job_assignment_rule
    )

    def position_assignment_rule(mdl, position):
        return sum(
            mdl.assignment[job, position] for job in mdl.jobs
        ) == 1

    model.position_assignment = pyo.Constraint(
        model.positions, rule=position_assignment_rule
    )

    # Anchor the first operation's start at time zero.
    model.time_origin = pyo.Constraint(
        expr=model.completion[0, 0] == model.duration[0, 0]
    )

    def workstation_precedence_rule(mdl, position, station):
        previous_completion = (
            mdl.completion[position, station - 1] if station > 0 else 0
        )
        return (
            mdl.completion[position, station]
            >= previous_completion + mdl.duration[position, station]
        )

    model.workstation_precedence = pyo.Constraint(
        model.positions,
        model.workstations,
        rule=workstation_precedence_rule,
    )

    def sequence_precedence_rule(mdl, position, station):
        if position == 0:
            return pyo.Constraint.Skip
        return (
            mdl.completion[position, station]
            >= mdl.completion[position - 1, station]
            + mdl.duration[position, station]
        )

    model.sequence_precedence = pyo.Constraint(
        model.positions,
        model.workstations,
        rule=sequence_precedence_rule,
    )

    model.makespan_objective = pyo.Objective(
        expr=model.completion[3, 2],
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPsi raises this when it cannot load a feasible solution.
        if "a feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.makespan_objective))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}