import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    n = 10
    stages = list(range(1, n + 1))

    a = params["a"]
    b = params["b"]
    c = params["c"]
    p = params["p"]
    q = params["q"]
    r = params["r"]

    req = {j: r[j - 1] for j in stages}
    horizon = range(1, n + 1)

    model = pyo.ConcreteModel()

    # x[j]: new tools purchased for use at stage j
    model.x = pyo.Var(horizon, domain=pyo.NonNegativeIntegers)

    # s[i,j]: tools that finish slow repair (sent after stage i) and return usable at stage j = i + p
    # indices: i in 1..n-p, j = i + p
    slow_pairs = [(i, i + p) for i in horizon if i + p <= n]
    model.slow = pyo.Var(slow_pairs, domain=pyo.NonNegativeIntegers)

    # f[i,j]: tools that finish fast repair (sent after stage i) and return usable at stage j = i + q
    fast_pairs = [(i, i + q) for i in horizon if i + q <= n]
    model.fast = pyo.Var(fast_pairs, domain=pyo.NonNegativeIntegers)

    # Availability: at each stage j, supply >= requirement
    def avail_rule(m, j):
        supply = m.x[j]
        for (i, jj) in slow_pairs:
            if jj == j:
                supply += m.slow[i, jj]
        for (i, jj) in fast_pairs:
            if jj == j:
                supply += m.fast[i, jj]
        return supply >= req[j]

    model.avail = pyo.Constraint(horizon, rule=avail_rule)

    # Tools used at stage j must be sent for repair afterward (all get repaired; no discarding).
    # Tools used at stage j = req[j] exactly (they are consumed/repaired). We need to allocate
    # each stage's tool usage to slow or fast repair.
    # For each stage j, the number of tools sent to slow + fast repair must equal req[j].
    # Slow repair after stage j is possible only if j + p <= n (if returns after horizon, useless but
    # still must be repaired — but repairing only costs money, so for minimization we allow "sent to
    # fast/slow" but if it returns after n it's wasted). To be safe and optimal, allow allocation.
    # However diverting to slow/fast when it returns after horizon costs more with no benefit, so
    # optimal won't do it. But we must ensure balance: total tools used at stage j = req[j].
    # Tools available at stage j are used; each used tool must be repaired (slow or fast).
    # We model repair-allocation variables per stage j: slow_j + fast_j = req[j].
    # But slow capacity in model is represented by slow[i,j+p] variables: tools returned.
    # So define: for stage j, slow-sent count = slow[i, i+p] where i=j; fast-sent = fast[j, j+q].
    # Since each stage sends exactly req[j] tools, we require:
    #   (slow var for j if exists) + (fast var for j if exists) = req[j]
    # But some stage j might not have either (if j+p > n and j+q > n). For n=10, p=3, q=1:
    # stage 10: fast return at 11 > 10 -> no fast var; slow return 13 > 10 -> no slow var.
    # Then tools used at stage 10 have nowhere to go. But they still must be repaired! Repair cost
    # must be incurred even if they never return. So we need separate cost/allocation variables.
    # Simpler: allocate slow/fast per stage regardless of return usability, but return vars only
    # for those that actually return within horizon.
    # Redesign: slow_sent[j] = tools sent to slow repair after stage j (cost b each).
    #           fast_sent[j] = tools sent to fast repair after stage j (cost c each).
    #           slow_sent[j] + fast_sent[j] = req[j]  (all used tools repaired)
    #           Returns: tools sent slow after stage i return at stage i+p (if <= n), usable then.
    #           tools sent fast after stage i return at i+q (if <= n), usable then.
    # This decouples "sending" from "returning within horizon".

    model.slow_sent = pyo.Var(horizon, domain=pyo.NonNegativeIntegers)
    model.fast_sent = pyo.Var(horizon, domain=pyo.NonNegativeIntegers)

    def split_rule(m, j):
        return m.slow_sent[j] + m.fast_sent[j] == req[j]

    model.split = pyo.Constraint(horizon, rule=split_rule)

    # Availability now uses slow_sent[i] for returns at i+p, fast_sent[i] for i+q
    def avail_rule2(m, j):
        supply = m.x[j]
        for i in horizon:
            if i + p == j:
                supply += m.slow_sent[i]
            if i + q == j:
                supply += m.fast_sent[i]
        return supply >= req[j]

    model.del_component(model.avail)
    model.avail = pyo.Constraint(horizon, rule=avail_rule2)

    # Remove old return vars (unused)
    model.del_component(model.slow)
    model.del_component(model.fast)

    # Objective: purchase cost + slow repair cost + fast repair cost
    def obj_rule(m):
        return (
            a * sum(m.x[j] for j in horizon)
            + b * sum(m.slow_sent[j] for j in horizon)
            + c * sum(m.fast_sent[j] for j in horizon)
        )

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}