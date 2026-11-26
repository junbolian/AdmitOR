# IR: {"sets":{"T":[0,1,2,3,4,5]},"params":{"demand":"length-6 sequence, ordered as 2-6,6-10,10-14,14-18,18-22,22-2"},"variables":{"staff_start[t]":"nonnegative integer; waiters starting an 8-hour shift in block t"},"constraints":["staff_start[t] + staff_start[(t-1)%6] >= demand[t] for every t in T"],"objective":"minimize sum(staff_start[t] for t in T)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    demand = params["demand"]
    if len(demand) != 6:
        raise ValueError("params['demand'] must contain exactly six entries.")

    model = pyo.ConcreteModel()
    model.blocks = pyo.RangeSet(0, 5)

    model.required_staff = pyo.Param(
        model.blocks,
        initialize={block: demand[block] for block in range(6)},
        within=pyo.NonNegativeReals,
    )

    # Each shift covers its starting block and the next block.
    # Integer variables ensure the solution counts whole waiters.
    model.staff_start = pyo.Var(
        model.blocks,
        domain=pyo.NonNegativeIntegers,
    )

    def coverage_rule(model, block):
        return (
            model.staff_start[block]
            + model.staff_start[(block - 1) % 6]
            >= model.required_staff[block]
        )

    model.coverage = pyo.Constraint(
        model.blocks,
        rule=coverage_rule,
    )

    model.total_waiters = pyo.Objective(
        expr=sum(model.staff_start[block] for block in model.blocks),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # Appsi raises this when it cannot load a feasible solution.
        # Unexpected solver exceptions propagate to the caller.
        if "a feasible solution was not found" not in str(exc).lower():
            raise

    # Success is determined solely by objective-value retrieval.
    try:
        obj_val = float(pyo.value(model.total_waiters))
    except (ValueError, TypeError):
        return {"objective": None, "status": "no_objective"}

    return {"objective": obj_val, "status": "optimal"}