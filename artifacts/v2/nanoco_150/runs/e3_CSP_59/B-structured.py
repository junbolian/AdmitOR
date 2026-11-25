# IR: {"sets":{"T":["28","38","21"],"P":"All nonnegative integer triples a with sum(length[t]*a[t] for t in T) <= bar_length; includes the zero triple"},"params":["bar_length","order_28","order_38","order_21","piece_length_28","piece_length_38","piece_length_21"],"variables":{"bars[p]":"NonNegativeIntegers for p in P"},"constraints":["For each t in T: sum(P[p][t]*bars[p] for p in P) == order[t]"],"objective":"Minimize sum(bars[p] for p in P)"}

from fractions import Fraction
from itertools import product

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    bar_length = Fraction(str(params["bar_length"]))
    piece_lengths = (
        Fraction(str(params["piece_length_28"])),
        Fraction(str(params["piece_length_38"])),
        Fraction(str(params["piece_length_21"])),
    )
    orders = (
        params["order_28"],
        params["order_38"],
        params["order_21"],
    )

    if bar_length <= 0 or any(length <= 0 for length in piece_lengths):
        return {"objective": None, "status": "invalid_lengths"}

    # Pattern bounds depend only on physical lengths, never on order quantities.
    count_ranges = [
        range(int(bar_length // length) + 1)
        for length in piece_lengths
    ]
    patterns = [
        counts
        for counts in product(*count_ranges)
        if sum(
            piece_lengths[type_index] * counts[type_index]
            for type_index in range(3)
        ) <= bar_length
    ]

    model = pyo.ConcreteModel()
    model.piece_types = pyo.Set(initialize=("28", "38", "21"), ordered=True)
    model.pattern_ids = pyo.Set(
        initialize=range(len(patterns)), ordered=True
    )

    type_positions = {"28": 0, "38": 1, "21": 2}

    model.demand = pyo.Param(
        model.piece_types,
        initialize={
            piece_type: orders[type_positions[piece_type]]
            for piece_type in model.piece_types
        },
        within=pyo.NonNegativeIntegers,
    )
    model.pattern_count = pyo.Param(
        model.pattern_ids,
        model.piece_types,
        initialize=lambda instance, pattern_id, piece_type: (
            patterns[pattern_id][type_positions[piece_type]]
        ),
        within=pyo.NonNegativeIntegers,
    )
    model.bars = pyo.Var(
        model.pattern_ids,
        domain=pyo.NonNegativeIntegers,
    )

    def exact_demand_rule(instance, piece_type):
        return sum(
            instance.pattern_count[pattern_id, piece_type]
            * instance.bars[pattern_id]
            for pattern_id in instance.pattern_ids
        ) == instance.demand[piece_type]

    model.exact_demand = pyo.Constraint(
        model.piece_types,
        rule=exact_demand_rule,
    )
    model.total_bars = pyo.Objective(
        expr=sum(model.bars[pattern_id] for pattern_id in model.pattern_ids),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPsi raises this when no feasible solution is available to load.
        # Other runtime errors remain visible to the calling harness.
        if "a feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "infeasible_or_failed"}
        raise

    try:
        obj_val = float(pyo.value(model.total_bars))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}