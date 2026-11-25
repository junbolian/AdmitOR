# IR: {"sets":{"T":["18","20","56"],"B":"range(sum(d[t] for t in T))"},"params":{"L":"params['standard_rebar_length']","d":{"18":"params['demand_18']","20":"params['demand_20']","56":"params['demand_56']"},"ell":{"18":"params['piece_length_18']","20":"params['piece_length_20']","56":"params['piece_length_56']"}},"variables":{"used[b]":"Binary","cuts[b,t]":"NonNegativeIntegers, upper bound d[t]"},"constraints":["For each t: sum_b cuts[b,t] == d[t].","For each b: sum_t ell[t]*cuts[b,t] <= L*used[b].","For each b,t: cuts[b,t] <= d[t]*used[b].","For each consecutive b,b+1: used[b] >= used[b+1]."],"objective":"Minimize sum_b used[b]."}
import math

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    segment_types = ("18", "20", "56")

    stock_length = float(params["standard_rebar_length"])
    raw_demands = {
        "18": params["demand_18"],
        "20": params["demand_20"],
        "56": params["demand_56"],
    }
    piece_lengths = {
        "18": float(params["piece_length_18"]),
        "20": float(params["piece_length_20"]),
        "56": float(params["piece_length_56"]),
    }

    if not math.isfinite(stock_length) or stock_length <= 0:
        return {"objective": None, "status": "invalid_parameters"}

    if any(
        not math.isfinite(piece_lengths[segment_type])
        or piece_lengths[segment_type] <= 0
        for segment_type in segment_types
    ):
        return {"objective": None, "status": "invalid_parameters"}

    demands = {}
    for segment_type in segment_types:
        raw_demand = raw_demands[segment_type]
        if not math.isfinite(raw_demand) or raw_demand < 0:
            return {"objective": None, "status": "invalid_parameters"}
        integer_demand = int(raw_demand)
        if integer_demand != raw_demand:
            return {"objective": None, "status": "invalid_parameters"}
        demands[segment_type] = integer_demand

    # One stock rebar per demanded piece is a sufficient finite upper bound.
    stock_count_bound = sum(demands.values())

    model = pyo.ConcreteModel()
    model.segment_types = pyo.Set(initialize=segment_types, ordered=True)
    model.stock_indices = pyo.Set(
        initialize=range(stock_count_bound), ordered=True
    )
    model.adjacent_indices = pyo.Set(
        initialize=range(max(0, stock_count_bound - 1)), ordered=True
    )

    model.used = pyo.Var(model.stock_indices, domain=pyo.Binary)

    def cut_bounds(instance, stock_index, segment_type):
        return (0, demands[segment_type])

    model.cuts = pyo.Var(
        model.stock_indices,
        model.segment_types,
        domain=pyo.NonNegativeIntegers,
        bounds=cut_bounds,
    )

    def exact_demand_rule(instance, segment_type):
        expression = (
            pyo.quicksum(
                instance.cuts[stock_index, segment_type]
                for stock_index in instance.stock_indices
            )
            == demands[segment_type]
        )
        # Empty index sets can produce a native Python Boolean.
        if isinstance(expression, bool):
            return pyo.Constraint.Feasible if expression else pyo.Constraint.Infeasible
        return expression

    model.exact_demand = pyo.Constraint(
        model.segment_types, rule=exact_demand_rule
    )

    def capacity_rule(instance, stock_index):
        return (
            pyo.quicksum(
                piece_lengths[segment_type]
                * instance.cuts[stock_index, segment_type]
                for segment_type in instance.segment_types
            )
            <= stock_length * instance.used[stock_index]
        )

    model.stock_capacity = pyo.Constraint(
        model.stock_indices, rule=capacity_rule
    )

    def activation_rule(instance, stock_index, segment_type):
        return (
            instance.cuts[stock_index, segment_type]
            <= demands[segment_type] * instance.used[stock_index]
        )

    model.cut_activation = pyo.Constraint(
        model.stock_indices,
        model.segment_types,
        rule=activation_rule,
    )

    def stock_order_rule(instance, stock_index):
        return instance.used[stock_index] >= instance.used[stock_index + 1]

    model.stock_order = pyo.Constraint(
        model.adjacent_indices, rule=stock_order_rule
    )

    model.stock_objective = pyo.Objective(
        expr=pyo.quicksum(
            model.used[stock_index]
            for stock_index in model.stock_indices
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as error:
        # APPSI raises this when it cannot load a feasible solution.
        # Leave success determination to objective retrieval below.
        if "A feasible solution was not found" not in str(error):
            raise

    try:
        obj_val = float(pyo.value(model.stock_objective))
    except (ValueError, TypeError):
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}