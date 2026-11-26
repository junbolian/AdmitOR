# IR: {"sets":{"I":"order indices","J":"standard-width indices","P":"all pairs (j,a) with a a nonzero vector of nonnegative integers and sum_i order_widths[i]*a[i] <= standard_widths[j]"},"params":{"order_widths":"params['order_widths']","order_lengths":"params['order_lengths']","standard_widths":"params['standard_widths']"},"variables":{"cut_length[p]":"continuous nonnegative length cut using pattern p"},"constraints":["For each i: sum_p pattern_count[p,i]*cut_length[p] = order_lengths[i]"],"objective":"minimize sum_p (standard_widths[standard_index[p]] - sum_i order_widths[i]*pattern_count[p,i])*cut_length[p]"}
from fractions import Fraction
from itertools import product

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Minimize trim-loss area using continuous cutting lengths."""

    # Exact rational arithmetic prevents rounding errors when enumerating
    # patterns that exactly fill a standard roll's width.
    order_widths = tuple(Fraction(str(value)) for value in params["order_widths"])
    order_lengths = tuple(Fraction(str(value)) for value in params["order_lengths"])
    standard_widths = tuple(
        Fraction(str(value)) for value in params["standard_widths"]
    )

    if (
        not order_widths
        or not standard_widths
        or len(order_widths) != len(order_lengths)
        or any(width <= 0 for width in order_widths)
        or any(length < 0 for length in order_lengths)
        or any(width <= 0 for width in standard_widths)
    ):
        return {"objective": None, "status": "invalid_params"}

    order_indices = range(len(order_widths))
    patterns = []

    for standard_index, standard_width in enumerate(standard_widths):
        count_ranges = [
            range(int(standard_width // order_widths[order_index]) + 1)
            for order_index in order_indices
        ]

        for counts in product(*count_ranges):
            if not any(counts):
                continue

            used_width = sum(
                (
                    order_widths[order_index] * counts[order_index]
                    for order_index in order_indices
                ),
                Fraction(0),
            )

            if used_width <= standard_width:
                patterns.append(
                    (standard_index, counts, standard_width - used_width)
                )

    model = pyo.ConcreteModel()
    model.orders = pyo.Set(initialize=order_indices, ordered=True)
    model.patterns = pyo.Set(initialize=range(len(patterns)), ordered=True)

    model.required_length = pyo.Param(
        model.orders,
        initialize={
            order_index: float(order_lengths[order_index])
            for order_index in order_indices
        },
        within=pyo.NonNegativeReals,
    )
    model.pattern_count = pyo.Param(
        model.patterns,
        model.orders,
        initialize={
            (pattern_index, order_index): patterns[pattern_index][1][order_index]
            for pattern_index in range(len(patterns))
            for order_index in order_indices
        },
        within=pyo.NonNegativeIntegers,
    )
    model.trim_width = pyo.Param(
        model.patterns,
        initialize={
            pattern_index: float(patterns[pattern_index][2])
            for pattern_index in range(len(patterns))
        },
        within=pyo.NonNegativeReals,
    )
    model.cut_length = pyo.Var(
        model.patterns,
        domain=pyo.NonNegativeReals,
    )

    def demand_rule(instance, order_index):
        # Tuple form remains a valid constraint when no patterns exist.
        return (
            instance.required_length[order_index],
            pyo.quicksum(
                instance.pattern_count[pattern_index, order_index]
                * instance.cut_length[pattern_index]
                for pattern_index in instance.patterns
            ),
            instance.required_length[order_index],
        )

    model.fulfill_orders = pyo.Constraint(model.orders, rule=demand_rule)

    model.total_trim_area = pyo.Objective(
        expr=pyo.quicksum(
            model.trim_width[pattern_index] * model.cut_length[pattern_index]
            for pattern_index in model.patterns
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPsi raises this error when it cannot load a feasible solution.
        # Other runtime errors remain visible to the calling harness.
        if "feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_trim_area))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}