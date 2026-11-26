# IR: {"sets":{"T":[0,1,2,3,4,5]},"params":{"min_waitstaff":"array of six minimum staffing requirements in chronological order, starting at 2am"},"variables":{"shift_starts[t]":{"type":"nonnegative_integer","index":"t in T","meaning":"waitstaff starting an eight-hour shift at the beginning of block t"}},"constraints":["shift_starts[t] + shift_starts[(t-1)%6] >= min_waitstaff[t], for each t in T"],"objective":{"sense":"minimize","expression":"sum(shift_starts[t] for t in T)"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    requirements = params["min_waitstaff"]

    model = pyo.ConcreteModel()
    model.blocks = pyo.RangeSet(0, 5)

    model.staffing_requirement = pyo.Param(
        model.blocks,
        initialize={
            block: requirements[block]
            for block in range(6)
        },
        within=pyo.NonNegativeReals,
    )

    model.shift_starts = pyo.Var(
        model.blocks,
        domain=pyo.NonNegativeIntegers,
    )

    def coverage_rule(instance, block):
        preceding_block = (block - 1) % 6
        return (
            instance.shift_starts[block]
            + instance.shift_starts[preceding_block]
            >= instance.staffing_requirement[block]
        )

    model.staffing_coverage = pyo.Constraint(
        model.blocks,
        rule=coverage_rule,
    )

    model.total_waitstaff = pyo.Objective(
        expr=sum(
            model.shift_starts[block]
            for block in model.blocks
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_waitstaff))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}