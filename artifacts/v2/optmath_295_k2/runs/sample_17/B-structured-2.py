# IR: {"sets":{"P":[0,1,2,3,4,5,6,7,8,9,10,11],"W":[1,2,3,4],"A":{"0":[1,2,4],"1":[1,2,4],"2":[3,4],"3":[1,2,3,4],"4":[3,4],"5":[1,2,3,4],"6":[1,2,3,4],"7":[1,2,4],"8":[1,2,3,4],"9":[1,2,3,4],"10":[2,3,4],"11":[2,3]}},"params":{"demand[w]":"params[demand_width_{w}], w in W","production[p,w]":"params[pattern_{p}_width_{w}], p in P, w in A[p]","limit[p]":"params[usage_limit_{p}], p in P"},"variables":{"uses[p]":"nonnegative integer, p in P"},"constraints":["sum(production[p,w]*uses[p] for p in P if w in A[p]) >= demand[w], w in W","uses[p] <= limit[p], p in P"],"objective":"minimize sum(uses[p] for p in P)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    pattern_widths = {
        0: (1, 2, 4),
        1: (1, 2, 4),
        2: (3, 4),
        3: (1, 2, 3, 4),
        4: (3, 4),
        5: (1, 2, 3, 4),
        6: (1, 2, 3, 4),
        7: (1, 2, 4),
        8: (1, 2, 3, 4),
        9: (1, 2, 3, 4),
        10: (2, 3, 4),
        11: (2, 3),
    }

    model = pyo.ConcreteModel()
    model.patterns = pyo.RangeSet(0, 11)
    model.widths = pyo.RangeSet(1, 4)
    model.production_pairs = pyo.Set(
        dimen=2,
        initialize=[
            (pattern, width)
            for pattern, widths in pattern_widths.items()
            for width in widths
        ],
    )

    model.demand = pyo.Param(
        model.widths,
        initialize={
            width: params[f"demand_width_{width}"]
            for width in model.widths
        },
    )
    model.production = pyo.Param(
        model.production_pairs,
        initialize={
            (pattern, width): params[f"pattern_{pattern}_width_{width}"]
            for pattern, width in model.production_pairs
        },
    )
    model.usage_limit = pyo.Param(
        model.patterns,
        initialize={
            pattern: params[f"usage_limit_{pattern}"]
            for pattern in model.patterns
        },
    )

    model.uses = pyo.Var(model.patterns, domain=pyo.NonNegativeIntegers)

    def demand_rule(instance, width):
        return sum(
            instance.production[pattern, width] * instance.uses[pattern]
            for pattern in instance.patterns
            if width in pattern_widths[pattern]
        ) >= instance.demand[width]

    model.demand_constraints = pyo.Constraint(
        model.widths, rule=demand_rule
    )
    model.usage_constraints = pyo.Constraint(
        model.patterns,
        rule=lambda instance, pattern: (
            instance.uses[pattern] <= instance.usage_limit[pattern]
        ),
    )
    model.total_rolls = pyo.Objective(
        expr=sum(model.uses[pattern] for pattern in model.patterns),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPsi raises this when automatic solution loading finds no solution.
        # Still determine success solely by retrieving the objective below.
        if "A feasible solution was not found" not in str(exc):
            raise

    try:
        obj_val = float(pyo.value(model.total_rolls))
    except ValueError:
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}