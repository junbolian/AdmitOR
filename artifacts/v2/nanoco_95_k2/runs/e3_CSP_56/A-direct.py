import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    stock_len = params["standard_rebar_length"]
    piece_lengths = [
        params["piece_length_18"],
        params["piece_length_20"],
        params["piece_length_56"],
    ]
    demands = [
        params["demand_18"],
        params["demand_20"],
        params["demand_56"],
    ]

    n_pieces = len(piece_lengths)

    # Number of patterns is bounded by the number of possible ways to place
    # pieces; we only need a generous upper bound. We enumerate all feasible
    # (a, b, c) count vectors with total length <= stock_len.
    max_counts = []
    for length in piece_lengths:
        max_counts.append(int(stock_len // length) if length > 0 else 0)

    feasible_patterns = []
    for a in range(max_counts[0] + 1):
        rem_a = stock_len - a * piece_lengths[0]
        if rem_a < 0:
            continue
        for b in range(max_counts[1] + 1):
            rem_b = rem_a - b * piece_lengths[1]
            if rem_b < 0:
                continue
            for c in range(max_counts[2] + 1):
                if b * piece_lengths[1] + c * piece_lengths[2] > rem_a:
                    continue
                if b * piece_lengths[1] + c * piece_lengths[2] <= rem_a:
                    used = a * piece_lengths[0] + b * piece_lengths[1] + c * piece_lengths[2]
                    if used <= stock_len:
                        feasible_patterns.append((a, b, c))

    # Provide an upper bound on number of stock bars used.
    total_len = sum(d * l for d, l in zip(demands, piece_lengths))
    n_bars_ub = int(total_len // stock_len) + sum(demands)
    if n_bars_ub < 1:
        n_bars_ub = 1

    pattern_list = feasible_patterns
    P = list(range(len(pattern_list)))
    B = list(range(n_bars_ub))

    model = pyo.ConcreteModel()

    model.P = pyo.Set(initialize=P)
    model.B = pyo.Set(initialize=B)

    # y[b] = 1 if bar b is used
    model.y = pyo.Var(model.B, within=pyo.Binary)

    # x[b, p] = 1 if bar b uses pattern p
    model.x = pyo.Var(model.B, model.P, within=pyo.Binary)

    def obj_rule(mdl):
        return pyo.summation(mdl.y)

    model.total_bars = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    # Each bar uses at most one pattern
    def one_pattern_rule(mdl, b):
        return sum(mdl.x[b, p] for p in mdl.P) <= mdl.y[b]

    model.one_pattern = pyo.Constraint(model.B, rule=one_pattern_rule)

    # Each bar used must have a pattern (optional since y in objective minimized
    # but keep for tightness); actually linking via <= is enough. Add implicit.

    # Demand satisfaction
    def demand_rule(mdl, i):
        return sum(
            pattern_list[p][i] * mdl.x[b, p]
            for b in mdl.B
            for p in mdl.P
        ) >= demands[i]

    model.demand = pyo.Constraint(range(n_pieces), rule=demand_rule)

    # Symmetry breaking: ordering of used bars
    def sym_rule(mdl, b):
        if b == 0:
            return pyo.Constraint.Skip
        return mdl.y[b] <= mdl.y[b - 1]

    model.symmetry = pyo.Constraint(model.B, rule=sym_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_bars))
    return {"objective": obj_val, "status": "optimal"}