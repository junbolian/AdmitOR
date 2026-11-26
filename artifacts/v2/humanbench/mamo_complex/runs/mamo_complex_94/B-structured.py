# IR: {"sets":{"days":"0..6 (Mon..Sun)","work_offsets":"0..4"},"params":{"requirements":"params['requirements'], seven daily staffing requirements in Mon..Sun order"},"variables":{"starts[d]":"nonnegative integer; employees beginning a five-day work period on day d"},"constraints":["For each day d: sum(starts[(d-k)%7] for k in work_offsets) >= requirements[d]."],"objective":"Minimize sum(starts[d] for d in days)."}
# Integer variables ensure that the solution hires whole employees.
# This is the integer linear formulation of the staffing problem.

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    requirements = params["requirements"]

    model = pyo.ConcreteModel()
    model.days = pyo.RangeSet(0, 6)
    model.work_offsets = pyo.RangeSet(0, 4)

    model.daily_requirements = pyo.Param(
        model.days,
        initialize={day: requirements[day] for day in range(7)},
        within=pyo.NonNegativeReals,
    )

    model.starts = pyo.Var(
        model.days,
        domain=pyo.NonNegativeIntegers,
    )

    def coverage_rule(instance, day):
        return (
            sum(
                instance.starts[(day - offset) % 7]
                for offset in instance.work_offsets
            )
            >= instance.daily_requirements[day]
        )

    model.daily_coverage = pyo.Constraint(
        model.days,
        rule=coverage_rule,
    )

    model.total_employees = pyo.Objective(
        expr=sum(model.starts[day] for day in model.days),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "A feasible solution was not found" not in str(exc):
            raise
        # Fall through and determine success only by objective retrieval.

    try:
        obj_val = float(pyo.value(model.total_employees))
    except ValueError:
        return {"objective": None, "status": "no_solution"}

    return {"objective": obj_val, "status": "optimal"}