# IR: {"sets":{"B":"0..5; shift starts at 2+4*b hours, modulo 24","K":"intervals partitioning [0,24) at every shift start and shift end, using 2:00 as time zero"},"params":{"demand_2_6":"params['demand_2_6']","demand_6_10":"params['demand_6_10']","demand_10_14":"params['demand_10_14']","demand_14_18":"params['demand_14_18']","demand_18_22":"params['demand_18_22']","demand_22_2":"params['demand_22_2']","salary_regular":"params['salary_regular']","salary_contract":"params['salary_contract']","shift_length":"params['shift_length']"},"derived":{"demand[b]":"demand for period b","full_days":"floor(shift_length/24)","remainder":"shift_length modulo 24","midpoint[k]":"midpoint of interval k","coverage[k,b]":"full_days + indicator((midpoint[k]-4*b) modulo 24 < remainder)","required[k]":"demand[floor(midpoint[k]/4)]"},"variables":{"regular[b]":"nonnegative integer; regular nurses starting daily in batch b","contract[b]":"nonnegative integer; contract nurses starting daily in batch b"},"constraints":["For each k: sum_b coverage[k,b]*(regular[b]+contract[b]) >= required[k]"],"objective":"minimize shift_length*sum_b(salary_regular*regular[b]+salary_contract*contract[b])"}

import math

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.batches = pyo.RangeSet(0, 5)

    model.demand = pyo.Param(
        model.batches,
        initialize={
            0: params["demand_2_6"],
            1: params["demand_6_10"],
            2: params["demand_10_14"],
            3: params["demand_14_18"],
            4: params["demand_18_22"],
            5: params["demand_22_2"],
        },
        within=pyo.NonNegativeReals,
    )
    model.salary_regular = pyo.Param(
        initialize=params["salary_regular"],
        within=pyo.NonNegativeReals,
    )
    model.salary_contract = pyo.Param(
        initialize=params["salary_contract"],
        within=pyo.NonNegativeReals,
    )
    model.shift_length = pyo.Param(
        initialize=params["shift_length"],
        within=pyo.PositiveReals,
    )

    # Time is measured from 2:00. Daily batches repeat cyclically.
    # Partitioning at shift ends also handles non-four-hour shift lengths.
    shift_hours = float(pyo.value(model.shift_length))
    full_days = math.floor(shift_hours / 24)
    remainder = shift_hours % 24

    boundaries = {0.0, 24.0}
    for batch in model.batches:
        start = 4.0 * batch
        boundaries.add(start)
        boundaries.add((start + remainder) % 24)

    ordered_boundaries = sorted(boundaries)
    midpoints = {
        interval: (
            ordered_boundaries[interval] + ordered_boundaries[interval + 1]
        ) / 2.0
        for interval in range(len(ordered_boundaries) - 1)
    }

    model.intervals = pyo.Set(
        initialize=range(len(midpoints)),
        ordered=True,
    )

    coverage_data = {
        (interval, batch): full_days
        + int((midpoints[interval] - 4.0 * batch) % 24 < remainder)
        for interval in model.intervals
        for batch in model.batches
    }
    required_data = {
        interval: pyo.value(
            model.demand[int(midpoints[interval] // 4)]
        )
        for interval in model.intervals
    }

    model.coverage = pyo.Param(
        model.intervals,
        model.batches,
        initialize=coverage_data,
        within=pyo.NonNegativeIntegers,
    )
    model.required = pyo.Param(
        model.intervals,
        initialize=required_data,
        within=pyo.NonNegativeReals,
    )

    model.regular = pyo.Var(
        model.batches,
        domain=pyo.NonNegativeIntegers,
    )
    model.contract = pyo.Var(
        model.batches,
        domain=pyo.NonNegativeIntegers,
    )

    def coverage_rule(instance, interval):
        return sum(
            instance.coverage[interval, batch]
            * (instance.regular[batch] + instance.contract[batch])
            for batch in instance.batches
        ) >= instance.required[interval]

    model.staffing_requirements = pyo.Constraint(
        model.intervals,
        rule=coverage_rule,
    )

    # Regular availability is unrestricted in the stated problem.
    # When contract pay is higher, replacing contract staff with regular
    # staff preserves coverage and reduces cost, so no contracts are needed.
    model.total_cost = pyo.Objective(
        expr=model.shift_length
        * sum(
            model.salary_regular * model.regular[batch]
            + model.salary_contract * model.contract[batch]
            for batch in model.batches
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}