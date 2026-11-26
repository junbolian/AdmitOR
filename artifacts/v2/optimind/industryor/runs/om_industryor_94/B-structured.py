# IR: {"sets":{"I":[290,315,350,455],"R":[0,1,2,3],"P":"nonzero integer vectors a with sum(a)<=max_pieces_per_raw and 0<=raw_pipe_length-sum(I[i]*a[i])<=max_leftover"},"params":{"raw_pipe_length":"params[raw_pipe_length]","demand":"params[demand_290,demand_315,demand_350,demand_455]","max_pattern_types":"params[max_pattern_types]","max_pieces_per_raw":"params[max_pieces_per_raw]","max_leftover":"params[max_leftover]","fraction":"params[extra_cost_fraction_most,extra_cost_fraction_second,extra_cost_fraction_third,extra_cost_fraction_fourth]","U":"sum(demand)"},"variables":{"x[p,r]":"nonnegative integer; pipes cut with pattern p at frequency rank r","y[p,r]":"binary; pattern p occupies rank r","total_cost":"nonnegative real; cost in raw-pipe value units"},"constraints":["For each i: sum(p,r,a[p,i]*x[p,r])>=demand[i] (surplus production allowed)","For each p,r: x[p,r]<=U*y[p,r]","For each p,r: x[p,r]>=y[p,r]","For each p: sum(r,y[p,r])<=1","For each r: sum(p,y[p,r])<=1","sum(p,r,y[p,r])<=max_pattern_types","For r=0,1,2: sum(p,x[p,r])>=sum(p,x[p,r+1])","total_cost=sum(p,r,(1+fraction[r])*x[p,r])"],"objective":"minimize total_cost"}
from itertools import product
from math import floor, isfinite

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    raw_pipe_length = float(params["raw_pipe_length"])
    demand_values = [
        params["demand_290"],
        params["demand_315"],
        params["demand_350"],
        params["demand_455"],
    ]
    pattern_limit_value = params["max_pattern_types"]
    piece_limit_value = params["max_pieces_per_raw"]
    max_leftover = float(params["max_leftover"])
    fractions = [
        float(params["extra_cost_fraction_most"]),
        float(params["extra_cost_fraction_second"]),
        float(params["extra_cost_fraction_third"]),
        float(params["extra_cost_fraction_fourth"]),
    ]

    integer_values = demand_values + [pattern_limit_value, piece_limit_value]
    if any(
        not isfinite(float(value))
        or float(value) < 0
        or not float(value).is_integer()
        for value in integer_values
    ):
        return {"objective": None, "status": "invalid_parameters"}

    demands = tuple(int(value) for value in demand_values)
    max_pattern_types = int(pattern_limit_value)
    max_pieces_per_raw = int(piece_limit_value)

    if (
        not isfinite(raw_pipe_length)
        or raw_pipe_length <= 0
        or not isfinite(max_leftover)
        or max_leftover < 0
        or any(not isfinite(value) or value < 0 for value in fractions)
        or max_pattern_types > len(fractions)
    ):
        return {"objective": None, "status": "invalid_parameters"}

    lengths = (290, 315, 350, 455)
    count_ranges = [
        range(min(max_pieces_per_raw, floor(raw_pipe_length / length)) + 1)
        for length in lengths
    ]

    patterns = []
    for counts in product(*count_ranges):
        if not 1 <= sum(counts) <= max_pieces_per_raw:
            continue
        used_length = sum(
            length * count for length, count in zip(lengths, counts)
        )
        leftover = raw_pipe_length - used_length
        if 0 <= leftover <= max_leftover:
            patterns.append(counts)

    # With nonnegative surcharges, an optimum exists using at most
    # sum(demands) pipes: repeatedly remove any pipe whose removal still
    # meets demand. Each remaining pipe can be charged to a demanded piece.
    upper_bound = sum(demands)

    model = pyo.ConcreteModel()
    model.product_types = pyo.Set(initialize=range(len(lengths)), ordered=True)
    model.patterns = pyo.Set(initialize=range(len(patterns)), ordered=True)
    model.ranks = pyo.Set(initialize=range(len(fractions)), ordered=True)
    model.adjacent_ranks = pyo.Set(
        initialize=range(len(fractions) - 1), ordered=True
    )

    model.pipe_count = pyo.Var(
        model.patterns, model.ranks, domain=pyo.NonNegativeIntegers
    )
    model.pattern_selected = pyo.Var(
        model.patterns, model.ranks, domain=pyo.Binary
    )
    model.total_cost = pyo.Var(domain=pyo.NonNegativeReals)

    def demand_rule(instance, product_idx):
        production = sum(
            patterns[pattern_idx][product_idx]
            * instance.pipe_count[pattern_idx, rank_idx]
            for pattern_idx in instance.patterns
            for rank_idx in instance.ranks
        )
        # Tuple form also represents a constant infeasible constraint
        # correctly when the admissible-pattern set is empty.
        return (demands[product_idx], production, None)

    model.demand_constraints = pyo.Constraint(
        model.product_types, rule=demand_rule
    )

    def activation_upper_rule(instance, pattern_idx, rank_idx):
        return (
            instance.pipe_count[pattern_idx, rank_idx]
            <= upper_bound * instance.pattern_selected[pattern_idx, rank_idx]
        )

    model.activation_upper = pyo.Constraint(
        model.patterns, model.ranks, rule=activation_upper_rule
    )

    def activation_lower_rule(instance, pattern_idx, rank_idx):
        return (
            instance.pipe_count[pattern_idx, rank_idx]
            >= instance.pattern_selected[pattern_idx, rank_idx]
        )

    model.activation_lower = pyo.Constraint(
        model.patterns, model.ranks, rule=activation_lower_rule
    )

    def unique_pattern_rule(instance, pattern_idx):
        return sum(
            instance.pattern_selected[pattern_idx, rank_idx]
            for rank_idx in instance.ranks
        ) <= 1

    model.unique_pattern_constraints = pyo.Constraint(
        model.patterns, rule=unique_pattern_rule
    )

    def unique_rank_rule(instance, rank_idx):
        return (
            None,
            sum(
                instance.pattern_selected[pattern_idx, rank_idx]
                for pattern_idx in instance.patterns
            ),
            1,
        )

    model.unique_rank_constraints = pyo.Constraint(
        model.ranks, rule=unique_rank_rule
    )

    model.pattern_limit = pyo.Constraint(
        expr=(
            None,
            sum(
                model.pattern_selected[pattern_idx, rank_idx]
                for pattern_idx in model.patterns
                for rank_idx in model.ranks
            ),
            max_pattern_types,
        )
    )

    def frequency_order_rule(instance, rank_idx):
        difference = sum(
            instance.pipe_count[pattern_idx, rank_idx]
            - instance.pipe_count[pattern_idx, rank_idx + 1]
            for pattern_idx in instance.patterns
        )
        return (0, difference, None)

    model.frequency_order = pyo.Constraint(
        model.adjacent_ranks, rule=frequency_order_rule
    )

    model.cost_definition = pyo.Constraint(
        expr=model.total_cost
        == sum(
            (1 + fractions[rank_idx])
            * model.pipe_count[pattern_idx, rank_idx]
            for pattern_idx in model.patterns
            for rank_idx in model.ranks
        )
    )
    model.total_cost_objective = pyo.Objective(
        expr=model.total_cost, sense=pyo.minimize
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # Appsi raises this when it cannot load a feasible solution.
        # Unexpected solver exceptions still propagate.
        if "a feasible solution was not found" not in str(exc).lower():
            raise

    try:
        obj_val = float(pyo.value(model.total_cost_objective))
    except (ValueError, TypeError):
        return {"objective": None, "status": "no_solution"}

    return {"objective": obj_val, "status": "optimal"}