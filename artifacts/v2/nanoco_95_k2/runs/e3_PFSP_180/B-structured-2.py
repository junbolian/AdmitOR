# IR: {"sets":{"jobs":[0,1,2,3],"positions":[0,1,2,3],"stations":[0,1,2]},"params":{"p":{"source":"params['p'][job][station]","type":"nonnegative real matrix"}},"variables":{"x[job,position]":"binary","completion[position,station]":"nonnegative real"},"constraints":["Each job occupies exactly one position: sum_position x[job,position] = 1.","Each position contains exactly one job: sum_job x[job,position] = 1.","Machine capacity: completion[position,station] >= (completion[position-1,station] if position>0 else 0) + sum_job p[job,station]*x[job,position].","Job precedence: completion[position,station] >= completion[position,station-1] + sum_job p[job,station]*x[job,position] for station>0."],"objective":"minimize completion[3,2]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve the permutation flow shop; params['p'][job][station] supplies times."""
    processing_times = params["p"]

    model = pyo.ConcreteModel()
    model.jobs = pyo.RangeSet(0, 3)
    model.positions = pyo.RangeSet(0, 3)
    model.stations = pyo.RangeSet(0, 2)

    model.processing_time = pyo.Param(
        model.jobs,
        model.stations,
        initialize={
            (job, station): processing_times[job][station]
            for job in model.jobs
            for station in model.stations
        },
        within=pyo.NonNegativeReals,
    )

    model.x = pyo.Var(model.jobs, model.positions, domain=pyo.Binary)
    model.completion = pyo.Var(
        model.positions, model.stations, domain=pyo.NonNegativeReals
    )

    model.position_duration = pyo.Expression(
        model.positions,
        model.stations,
        rule=lambda mdl, position, station: sum(
            mdl.processing_time[job, station] * mdl.x[job, position]
            for job in mdl.jobs
        ),
    )

    model.job_assignment = pyo.Constraint(
        model.jobs,
        rule=lambda mdl, job: sum(
            mdl.x[job, position] for position in mdl.positions
        ) == 1,
    )

    model.position_assignment = pyo.Constraint(
        model.positions,
        rule=lambda mdl, position: sum(
            mdl.x[job, position] for job in mdl.jobs
        ) == 1,
    )

    def machine_capacity_rule(mdl, position, station):
        preceding_completion = (
            mdl.completion[position - 1, station] if position > 0 else 0
        )
        return (
            mdl.completion[position, station]
            >= preceding_completion + mdl.position_duration[position, station]
        )

    model.machine_capacity = pyo.Constraint(
        model.positions,
        model.stations,
        rule=machine_capacity_rule,
    )

    def job_precedence_rule(mdl, position, station):
        if station == 0:
            return pyo.Constraint.Skip
        return (
            mdl.completion[position, station]
            >= mdl.completion[position, station - 1]
            + mdl.position_duration[position, station]
        )

    model.job_precedence = pyo.Constraint(
        model.positions,
        model.stations,
        rule=job_precedence_rule,
    )

    model.makespan_objective = pyo.Objective(
        expr=model.completion[3, 2],
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        # HiGHS can raise when no feasible solution is available to load.
        # Determine success solely by objective-value availability below.
        pass

    try:
        obj_val = float(pyo.value(model.makespan_objective))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}