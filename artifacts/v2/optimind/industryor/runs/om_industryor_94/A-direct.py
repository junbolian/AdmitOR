import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    raw_len = params["raw_pipe_length"]
    demand = {
        290: params["demand_290"],
        315: params["demand_315"],
        350: params["demand_350"],
        455: params["demand_455"],
    }
    max_patterns = params["max_pattern_types"]
    max_pieces = params["max_pieces_per_raw"]
    max_leftover = params["max_leftover"]
    frac = [
        params["extra_cost_fraction_most"],
        params["extra_cost_fraction_second"],
        params["extra_cost_fraction_third"],
        params["extra_cost_fraction_fourth"],
    ]

    lengths = [290, 315, 350, 455]
    n_len = len(lengths)

    # Enumerate all feasible cutting patterns
    patterns = []

    def gen_patterns(idx, counts, used_len, used_pieces):
        if idx == n_len:
            leftover = raw_len - used_len
            if leftover >= 0 and leftover <= max_leftover and used_pieces >= 1:
                patterns.append(tuple(counts))
            return
        L = lengths[idx]
        max_c = min(demand[L], max_pieces - used_pieces, (raw_len - used_len) // L)
        for c in range(max_c + 1):
            counts.append(c)
            gen_patterns(idx + 1, counts, used_len + c * L, used_pieces + c)
            counts.pop()

    gen_patterns(0, [], 0, 0)

    if not patterns:
        return {"objective": None, "status": "no feasible patterns"}

    n_pat = len(patterns)
    pat_index = list(range(n_pat))

    model = pyo.ConcreteModel()

    model.P = pyo.Set(initialize=pat_index, ordered=True)
    model.K = pyo.Set(initialize=list(range(max_patterns)), ordered=True)
    model.L = pyo.Set(initialize=list(range(n_len)), ordered=True)

    # y[k, p] = 1 if pattern p is assigned to slot k (distinct pattern usage slot)
    model.y = pyo.Var(model.K, model.P, domain=pyo.Binary)
    # x[p] = number of raw pipes cut using pattern p
    model.x = pyo.Var(model.P, domain=pyo.NonNegativeIntegers)
    # z[k] = indicator slot k is used
    model.z = pyo.Var(model.K, domain=pyo.Binary)
    # u[k] = usage count assigned to slot k
    model.u = pyo.Var(model.K, domain=pyo.NonNegativeReals)

    # Each pattern's x must be tied to exactly one slot (or zero if pattern unused)
    # If x[p] > 0 then some y[k,p] = 1, and then x[p] = u[k].
    # Enforce: x[p] <= BigM * sum_k y[k,p]
    big_m = sum(demand[L] for L in lengths) * 10 + 100

    def assign_rule(mdl, p):
        return mdl.x[p] <= big_m * sum(mdl.y[k, p] for k in mdl.K)
    model.assign_con = pyo.Constraint(model.P, rule=assign_rule)

    # Each slot k used by at most one pattern
    def slot_rule(mdl, k):
        return sum(mdl.y[k, p] for p in mdl.P) <= 1
    model.slot_con = pyo.Constraint(model.K, rule=slot_rule)

    # Link z[k] and y
    def z_link_rule(mdl, k):
        return mdl.z[k] == sum(mdl.y[k, p] for p in mdl.P)
    model.z_link = pyo.Constraint(model.K, rule=z_link_rule)

    # Link u[k] to x: if pattern p in slot k then u[k] == x[p]
    # u[k] = sum_p x[p] * y[k,p]
    def u_link_rule(mdl, k):
        return mdl.u[k] == sum(mdl.x[p] * mdl.y[k, p] for p in mdl.P)
    model.u_link = pyo.Constraint(model.K, rule=u_link_rule)

    # Slots must be ordered by usage: u[0] >= u[1] >= u[2] >= u[3]
    def order_rule(mdl, k):
        if k < max_patterns - 1:
            return mdl.u[k] >= mdl.u[k + 1]
        return pyo.Constraint.Skip
    model.order_con = pyo.Constraint(model.K, rule=order_rule)

    # filled slots form a prefix: z[k] >= z[k+1]
    def prefix_rule(mdl, k):
        if k < max_patterns - 1:
            return mdl.z[k] >= mdl.z[k + 1]
        return pyo.Constraint.Skip
    model.prefix_con = pyo.Constraint(model.K, rule=prefix_rule)

    # Demand satisfaction
    def demand_rule(mdl, li):
        L = lengths[li]
        return sum(patterns[p][li] * mdl.x[p] for p in mdl.P) >= demand[L]
    model.demand_con = pyo.Constraint(model.L, rule=demand_rule)

    # Objective: total raw pipe cost (each raw pipe value normalized to 1) plus extra costs
    # Extra cost: for slot k with usage u[k] > 0, extra = frac[k] * 1 * z[k]
    obj_expr = sum(model.x[p] for p in model.P)
    for k in model.K:
        obj_expr += frac[k] * model.z[k]
    model.obj = pyo.Objective(expr=obj_expr, sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}