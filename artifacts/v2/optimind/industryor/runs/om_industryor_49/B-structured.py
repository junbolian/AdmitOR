# IR: {"sets":{"P":"range(params['num_periods'])","S":"range(params['num_shift_starts'])"},"params":{"demand":"required nurses in each period","regular_wage":"regular hourly wage","contract_wage":"contract hourly wage","shift_hours":"shift duration","num_periods":"frozen at 6","num_shift_starts":"frozen at 6"},"structure":{"period_hours":4,"shift_requirement":"shift_hours is a positive multiple of 4 and at most 24","coverage":"A[p,s]=1 iff (p-s) mod num_periods < shift_hours/4"},"variables":{"regular[s]":"nonnegative integer","contract[s]":"nonnegative integer"},"constraints":["For every p in P: sum(A[p,s]*(regular[s]+contract[s]) for s in S) >= demand[p]"],"objective":"minimize shift_hours*sum(regular_wage*regular[s]+contract_wage*contract[s] for s in S)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    demand = params["demand"]
    regular_wage = params["regular_wage"]
    contract_wage = params["contract_wage"]
    shift_hours = params["shift_hours"]
    num_periods = params["num_periods"]
    num_shift_starts = params["num_shift_starts"]

    # Six daily periods and six starting batches are frozen structure.
    if num_periods != 6 or num_shift_starts != 6:
        return {"objective": None, "status": "invalid_dimensions"}

    period_hours = 4
    if (
        shift_hours <= 0
        or shift_hours > period_hours * num_periods
        or shift_hours % period_hours != 0
    ):
        return {"objective": None, "status": "invalid_shift_hours"}

    periods_per_shift = int(shift_hours / period_hours)

    model = pyo.ConcreteModel()
    model.periods = pyo.RangeSet(0, int(num_periods) - 1)
    model.starts = pyo.RangeSet(0, int(num_shift_starts) - 1)

    model.required_staff = pyo.Param(
        model.periods,
        initialize={period: demand[period] for period in model.periods},
        within=pyo.NonNegativeReals,
    )
    model.regular_hourly_pay = pyo.Param(
        initialize=regular_wage, within=pyo.Reals
    )
    model.contract_hourly_pay = pyo.Param(
        initialize=contract_wage, within=pyo.Reals
    )
    model.hours_per_shift = pyo.Param(
        initialize=shift_hours, within=pyo.PositiveReals
    )
    model.coverage = pyo.Param(
        model.periods,
        model.starts,
        initialize={
            (period, start): int(
                (period - start) % int(num_periods) < periods_per_shift
            )
            for period in model.periods
            for start in model.starts
        },
        within=pyo.Binary,
    )

    model.regular = pyo.Var(model.starts, domain=pyo.NonNegativeIntegers)
    model.contract = pyo.Var(model.starts, domain=pyo.NonNegativeIntegers)

    def coverage_rule(instance, period):
        return sum(
            instance.coverage[period, start]
            * (instance.regular[start] + instance.contract[start])
            for start in instance.starts
        ) >= instance.required_staff[period]

    model.staffing_requirement = pyo.Constraint(
        model.periods, rule=coverage_rule
    )

    model.total_cost = pyo.Objective(
        expr=model.hours_per_shift
        * sum(
            model.regular_hourly_pay * model.regular[start]
            + model.contract_hourly_pay * model.contract[start]
            for start in model.starts
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