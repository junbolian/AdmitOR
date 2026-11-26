# IR: {"sets":{"T":[0,1,2,3,4,5]},"params":{"requirements":"six-element sequence indexed by T","shift_length":"positive working hours","period_length":"positive hours per period","K":"shift_length / period_length; must be an integer in [1,6]"},"variables":{"crew_start[t]":"nonnegative integer for t in T"},"constraints":["coverage[t]: sum(crew_start[(t-offset) mod 6] for offset in range(K)) >= requirements[t], for each t in T"],"objective":"minimize sum(crew_start[t] for t in T)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    requirements = params["requirements"]
    shift_length = params["shift_length"]
    period_length = params["period_length"]

    periods = tuple(range(6))
    period_count = len(periods)

    if len(requirements) != period_count:
        return {"objective": None, "status": "invalid_requirements"}

    if shift_length <= 0 or period_length <= 0:
        return {"objective": None, "status": "invalid_lengths"}

    coverage_ratio = shift_length / period_length
    if not 1 <= coverage_ratio <= period_count:
        return {"objective": None, "status": "invalid_shift_length"}

    coverage_count = int(coverage_ratio)
    if coverage_count != coverage_ratio:
        return {"objective": None, "status": "nonintegral_shift_length"}

    model = pyo.ConcreteModel()
    model.periods = pyo.Set(initialize=periods, ordered=True)

    model.required_crew = pyo.Param(
        model.periods,
        initialize={
            period: requirements[period]
            for period in periods
        },
        within=pyo.NonNegativeReals,
    )

    model.crew_start = pyo.Var(
        model.periods,
        domain=pyo.NonNegativeIntegers,
    )

    def coverage_rule(instance, period):
        return (
            sum(
                instance.crew_start[(period - offset) % period_count]
                for offset in range(coverage_count)
            )
            >= instance.required_crew[period]
        )

    model.coverage = pyo.Constraint(
        model.periods,
        rule=coverage_rule,
    )

    model.total_crew = pyo.Objective(
        expr=sum(model.crew_start[period] for period in model.periods),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as error:
        # Appsi raises this when it cannot load a feasible solution.
        if "a feasible solution was not found" in str(error).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_crew))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}