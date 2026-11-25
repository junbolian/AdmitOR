# IR: {"sets":{"P":"0..11","W":"0..3 (widths 1..4)"},"params":{"demand":"demand[w], nonnegative; length-4 sequence","pattern_usage_limit":"pattern_usage_limit[p], nonnegative; length-12 sequence","pattern_yield":"pattern_yield[p][w], nonnegative; 12-by-4 sequence"},"variables":{"uses[p]":"nonnegative integer"},"constraints":["For each w in W: sum(pattern_yield[p,w]*uses[p] for p in P) >= demand[w].","For each p in P: uses[p] <= pattern_usage_limit[p]."],"objective":"Minimize sum(uses[p] for p in P)."}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve using width-ordered demand and pattern-major yield sequences."""
    demand = params["demand"]
    pattern_usage_limit = params["pattern_usage_limit"]
    pattern_yield = params["pattern_yield"]

    model = pyo.ConcreteModel()
    model.patterns = pyo.RangeSet(0, 11)
    model.widths = pyo.RangeSet(0, 3)

    model.required_units = pyo.Param(
        model.widths,
        initialize={w: demand[w] for w in model.widths},
        within=pyo.NonNegativeReals,
    )
    model.usage_caps = pyo.Param(
        model.patterns,
        initialize={p: pattern_usage_limit[p] for p in model.patterns},
        within=pyo.NonNegativeReals,
    )
    model.yields = pyo.Param(
        model.patterns,
        model.widths,
        initialize={
            (p, w): pattern_yield[p][w]
            for p in model.patterns
            for w in model.widths
        },
        within=pyo.NonNegativeReals,
    )

    model.uses = pyo.Var(model.patterns, domain=pyo.NonNegativeIntegers)

    def demand_rule(instance, w):
        return (
            sum(
                instance.yields[p, w] * instance.uses[p]
                for p in instance.patterns
            )
            >= instance.required_units[w]
        )

    model.demand_requirements = pyo.Constraint(
        model.widths, rule=demand_rule
    )
    model.pattern_limits = pyo.Constraint(
        model.patterns,
        rule=lambda instance, p: instance.uses[p] <= instance.usage_caps[p],
    )
    model.total_rolls = pyo.Objective(
        expr=sum(model.uses[p] for p in model.patterns),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "infeasible_or_failed"}

    try:
        obj_val = float(pyo.value(model.total_rolls))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}