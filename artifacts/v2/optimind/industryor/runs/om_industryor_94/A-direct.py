import itertools

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    raw_len = params["raw_pipe_length"]
    demands = {
        290: params["demand_290"],
        315: params["demand_315"],
        350: params["demand_350"],
        455: params["demand_455"],
    }
    max_patterns = int(params["max_pattern_types"])
    max_pieces = int(params["max_pieces_per_raw"])
    max_leftover = params["max_leftover"]

    lengths = [290, 315, 350, 455]
    n_len = len(lengths)

    # Enumerate feasible cutting patterns: counts per length, total pieces
    # <= max_pieces, leftover <= max_leftover.
    feasible = []
    for counts in itertools.product(range(max_pieces + 1), repeat=n_len):
        total = sum(counts)
        if total == 0 or total > max_pieces:
            continue
        used = sum(counts[i] * lengths[i] for i in range(n_len))
        if used > raw_len:
            continue
        if raw_len - used > max_leftover:
            continue
        feasible.append(counts)

    n_pat = len(feasible)

    model = pyo.ConcreteModel()

    model.P = pyo.RangeSet(0, n_pat - 1)
    model.L = pyo.RangeSet(0, n_len - 1)

    # Number of raw pipes cut using each pattern.
    model.x = pyo.Var(model.P, domain=pyo.NonNegativeIntegers)
    # y[p] = 1 if pattern p is used.
    model.y = pyo.Var(model.P, domain=pyo.Binary)

    # z[p, r] = 1 if pattern p occupies frequency-rank r (0 = most frequent).
    n_rank = n_len
    model.R = pyo.RangeSet(0, n_rank - 1)
    model.z = pyo.Var(model.P, model.R, domain=pyo.Binary)

    extra_frac = [
        params["extra_cost_fraction_most"],
        params["extra_cost_fraction_second"],
        params["extra_cost_fraction_third"],
        params["extra_cost_fraction_fourth"],
    ]

    total_demand = sum(demands[l] for l in lengths)
    # Safe upper bound on raw pipes of any single pattern.
    big_m = total_demand + 1

    def demand_rule(mdl, i):
        return sum(feasible[p][i] * mdl.x[p] for p in range(n_pat)) >= demands[lengths[i]]

    model.demand_con = pyo.Constraint(model.L, rule=demand_rule)

    model.npat_con = pyo.Constraint(
        expr=sum(model.y[p] for p in range(n_pat)) <= max_patterns
    )

    def link_rule(mdl, p):
        return mdl.x[p] <= big_m * mdl.y[p]

    model.link_con = pyo.Constraint(model.P, rule=link_rule)

    def rank_assign_rule(mdl, p):
        return sum(mdl.z[p, r] for r in range(n_rank)) == mdl.y[p]

    model.rank_assign_con = pyo.Constraint(model.P, rule=rank_assign_rule)

    # Frequency ordering: rank r (more frequent) must have >= count than rank r+1.
    rank_pairs = [
        (p, q, r)
        for p in range(n_pat)
        for q in range(n_pat)
        for r in range(n_rank - 1)
        if p != q
    ]
    model.Zr = pyo.Set(initialize=rank_pairs, dimen=3)

    def ordering_rule(mdl, p, q, r):
        return mdl.x[p] - mdl.x[q] >= 1 - big_m * (2 - mdl.z[p, r] - mdl.z[q, r + 1])

    model.ordering_con = pyo.Constraint(model.Zr, rule=ordering_rule)

    # u[r] indicates whether rank r is occupied.
    model.u = pyo.Var(model.R, domain=pyo.Binary)

    def u_rule(mdl, r):
        return mdl.u[r] == sum(mdl.z[p, r] for p in range(n_pat))

    model.u_con = pyo.Constraint(model.R, rule=u_rule)

    def contig_rule(mdl, r):
        return mdl.u[r] >= mdl.u[r + 1]

    model.contig_con = pyo.Constraint(pyo.RangeSet(0, n_rank - 2), rule=contig_rule)

    # Linearized cost:
    #   base cost = sum(x[p])
    #   extra cost = sum over ranks r of extra_frac[r] * (sum_p w[p,r])
    # with w[p,r] = x[p] if z[p,r]=1 else 0, bounded by big_m.
    model.w = pyo.Var(model.P, model.R, domain=pyo.NonNegativeReals)

    def w_upper(mdl, p, r):
        return mdl.w[p, r] <= big_m * mdl.z[p, r]

    def w_lower(mdl, p, r):
        return mdl.w[p, r] >= mdl.x[p] - big_m * (1 - mdl.z[p, r])

    def w_zero(mdl, p, r):
        return mdl.w[p, r] <= mdl.x[p]

    model.w_upper_con = pyo.Constraint(model.P, model.R, rule=w_upper)
    model.w_lower_con = pyo.Constraint(model.P, model.R, rule=w_lower)
    model.w_zero_con = pyo.Constraint(model.P, model.R, rule=w_zero)

    def obj_rule(mdl):
        base = sum(mdl.x[p] for p in range(n_pat))
        extra = sum(
            extra_frac[r] * sum(mdl.w[p, r] for p in range(n_pat))
            for r in range(n_rank)
        )
        return base + extra

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}