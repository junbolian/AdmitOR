# IR: {"sets":{"I":"orders","S":"stock widths","P":"all (s,a) with s in S, a in nonnegative integers^I, sum(a)>0, and sum(order_widths[i]*a[i])<=stock_widths[s]"},"params":{"order_widths":"positive widths indexed by I","order_lengths":"nonnegative required lengths indexed by I","stock_widths":"positive widths indexed by S"},"variables":{"cut_length[p]":"nonnegative continuous length cut using pattern p"},"constraints":["For each i in I: sum(a[p,i]*cut_length[p] for p in P) = order_lengths[i]"],"objective":"Minimize sum((stock_widths[s[p]]-sum(order_widths[i]*a[p,i] for i in I))*cut_length[p] for p in P)"}

from fractions import Fraction
from itertools import product

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    order_widths = tuple(
        Fraction(str(value)) for value in params["order_widths"]
    )
    order_lengths = tuple(
        Fraction(str(value)) for value in params["order_lengths"]
    )
    stock_widths = tuple(
        Fraction(str(value)) for value in params["stock_widths"]
    )

    if (
        not order_widths
        or not stock_widths
        or len(order_widths) != len(order_lengths)
        or any(value <= 0 for value in order_widths)
        or any(value < 0 for value in order_lengths)
        or any(value <= 0 for value in stock_widths)
    ):
        return {"objective": None, "status": "invalid_parameters"}

    order_indices = range(len(order_widths))
    patterns = []

    # Enumerate every feasible, nonempty cross-sectional cutting pattern.
    # Fractions avoid floating-point errors in width feasibility tests.
    for stock_idx, stock_width in enumerate(stock_widths):
        count_ranges = [
            range(int(stock_width // order_widths[order_idx]) + 1)
            for order_idx in order_indices
        ]

        for counts in product(*count_ranges):
            if not any(counts):
                continue

            used_width = sum(
                order_widths[order_idx] * counts[order_idx]
                for order_idx in order_indices
            )
            if used_width <= stock_width:
                patterns.append(
                    (stock_idx, counts, stock_width - used_width)
                )

    model = pyo.ConcreteModel()
    model.orders = pyo.Set(initialize=order_indices, ordered=True)
    model.patterns = pyo.Set(
        initialize=range(len(patterns)), ordered=True
    )

    # Continuous lengths implement unlimited stock length and splicing.
    model.cut_length = pyo.Var(
        model.patterns, domain=pyo.NonNegativeReals
    )

    def required_length_rule(instance, order_idx):
        supplied_length = pyo.quicksum(
            patterns[pattern_idx][1][order_idx]
            * instance.cut_length[pattern_idx]
            for pattern_idx in instance.patterns
        )
        required_length = float(order_lengths[order_idx])
        # Tuple form also supports an order with no feasible pattern.
        return (required_length, supplied_length, required_length)

    model.required_length = pyo.Constraint(
        model.orders, rule=required_length_rule
    )

    model.waste_area = pyo.Objective(
        expr=pyo.quicksum(
            float(patterns[pattern_idx][2])
            * model.cut_length[pattern_idx]
            for pattern_idx in model.patterns
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "A feasible solution was not found" in str(exc):
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.waste_area))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}