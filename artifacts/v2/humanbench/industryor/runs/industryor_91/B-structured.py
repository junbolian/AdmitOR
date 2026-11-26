# IR: {"sets":{"S":[1,2,3,4,5,6],"E":"sorted unique daily shift boundaries and work-end times modulo T","K":"consecutive intervals between E points"},"params":{"req[s]":"params['req_'+str(s)]","L":"params['shift_length']","h":"4 hours per demand period (structural)","T":"6*h","t[k]":"midpoint of interval k","A[k,s]":"floor((t[k]-h*(s-1))/T)-floor((t[k]-h*(s-1)-L)/T)"},"variables":{"x[s]":"nonnegative integer number starting each day at shift s"},"constraints":["For each k in K: sum(A[k,s]*x[s] for s in S) >= req[floor(t[k]/h)+1]."],"objective":"Minimize sum(x[s] for s in S)."}

import math

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Minimize daily staffing for a repeating, continuous-coverage schedule."""
    shift_ids = tuple(range(1, 7))
    period_hours = 4
    day_hours = len(shift_ids) * period_hours

    requirements = {
        1: float(params["req_1"]),
        2: float(params["req_2"]),
        3: float(params["req_3"]),
        4: float(params["req_4"]),
        5: float(params["req_5"]),
        6: float(params["req_6"]),
    }
    work_hours = float(params["shift_length"])

    if not math.isfinite(work_hours) or work_hours < 0:
        return {"objective": None, "status": "invalid_shift_length"}

    if any(
        not math.isfinite(required) or required < 0
        for required in requirements.values()
    ):
        return {"objective": None, "status": "invalid_requirement"}

    start_times = {
        shift_id: period_hours * (shift_id - 1)
        for shift_id in shift_ids
    }

    # Coverage and demand are constant between these event times.
    # Including work-end times handles durations that are not multiples
    # of four hours without treating partial coverage as full coverage.
    event_times = {0, day_hours}
    event_times.update(start_times.values())
    event_times.update(
        (start_times[shift_id] + work_hours) % day_hours
        for shift_id in shift_ids
    )
    ordered_events = sorted(event_times)

    midpoints = {
        interval_id: (left + right) / 2
        for interval_id, (left, right) in enumerate(
            zip(ordered_events[:-1], ordered_events[1:])
        )
    }

    # Count active daily cohorts at each midpoint. This also supports
    # work durations exceeding one day.
    coverage = {
        (interval_id, shift_id): (
            math.floor(
                (midpoint - start_times[shift_id]) / day_hours
            )
            - math.floor(
                (midpoint - start_times[shift_id] - work_hours) / day_hours
            )
        )
        for interval_id, midpoint in midpoints.items()
        for shift_id in shift_ids
    }
    demand_period = {
        interval_id: math.floor(midpoint / period_hours) + 1
        for interval_id, midpoint in midpoints.items()
    }

    model = pyo.ConcreteModel()
    model.shifts = pyo.Set(initialize=shift_ids, ordered=True)
    model.intervals = pyo.Set(initialize=tuple(midpoints), ordered=True)

    model.requirement = pyo.Param(
        model.shifts,
        initialize=requirements,
        within=pyo.NonNegativeReals,
    )
    model.coverage_coefficient = pyo.Param(
        model.intervals,
        model.shifts,
        initialize=coverage,
        within=pyo.NonNegativeIntegers,
    )
    model.starts = pyo.Var(
        model.shifts,
        domain=pyo.NonNegativeIntegers,
    )

    def coverage_rule(problem, interval_id):
        return (
            sum(
                problem.coverage_coefficient[interval_id, shift_id]
                * problem.starts[shift_id]
                for shift_id in problem.shifts
            )
            >= problem.requirement[demand_period[interval_id]]
        )

    model.staffing_coverage = pyo.Constraint(
        model.intervals,
        rule=coverage_rule,
    )
    model.total_staff = pyo.Objective(
        expr=sum(model.starts[shift_id] for shift_id in model.shifts),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_staff))
    except (ValueError, TypeError):
        return {"objective": None, "status": "no_objective"}

    return {"objective": obj_val, "status": "optimal"}