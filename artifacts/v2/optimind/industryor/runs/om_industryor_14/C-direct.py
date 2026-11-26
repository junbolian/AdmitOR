import gurobipy as gp
from gurobipy import GRB

def solve(params):
    a = params["a"]
    b = params["b"]
    c = params["c"]
    p = params["p"]
    q = params["q"]
    r = params["r"]

    n = len(r)
    # stages are 1-indexed internally; use 0-indexed lists
    # r[j] = requirement at stage j+1 (0-indexed: stage index i means stage i+1)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Decision variables (0-indexed: i = 0..n-1 corresponds to stage i+1)
    # x[i]: new tools purchased at stage i
    # s[i]: tools sent to slow repair after stage i
    # f[i]: tools sent to fast repair after stage i
    x = model.addVars(n, vtype=GRB.INTEGER, lb=0, name="x")
    s = model.addVars(n, vtype=GRB.INTEGER, lb=0, name="s")
    f = model.addVars(n, vtype=GRB.INTEGER, lb=0, name="f")

    # Objective: minimize total cost
    model.setObjective(
        gp.quicksum(a * x[i] + b * s[i] + c * f[i] for i in range(n)),
        GRB.MINIMIZE
    )

    # At each stage i, the tools available are:
    # - new tools purchased this stage: x[i]
    # - tools returned from slow repair: sent to slow repair after stage i-p (0-indexed: i-p),
    #   i.e., s[i-p] if i-p >= 0
    # - tools returned from fast repair: sent to fast repair after stage i-q (0-indexed: i-q),
    #   i.e., f[i-q] if i-q >= 0
    # These must cover the requirement r[i] (0-indexed)

    for i in range(n):
        available = x[i]
        # slow repair: tool sent after stage j (0-indexed) returns at stage j+p (0-indexed)
        # so returns at stage i if j = i - p
        j_slow = i - p
        if j_slow >= 0:
            available = available + s[j_slow]
        # fast repair: tool sent after stage j returns at stage j+q
        j_fast = i - q
        if j_fast >= 0:
            available = available + f[j_fast]

        model.addConstr(available >= r[i], name=f"demand_{i}")

    # After each stage i, tools used must all be sent to either slow or fast repair
    # (or discarded, but since there's no salvage value and tools cost money, optimal
    # solution won't discard — but to be correct we allow that tools used = r[i],
    # and we must send AT MOST r[i] to repair; we cannot send more than used)
    # Actually: tools available at stage i = x[i] + returned repairs
    # All r[i] tools used at stage i must be repaired; additional purchased/available tools
    # beyond r[i] could also be repaired or held. But there's no holding variable —
    # let's think more carefully.
    #
    # The correct formulation: at stage i, let avail[i] = x[i] + s[i-p] + f[i-q]
    # avail[i] >= r[i] (demand constraint)
    # Tools actually used = r[i]; excess tools (avail[i] - r[i]) can also be sent to repair.
    # s[i] + f[i] <= avail[i]  (can't send more to repair than available)
    # But also we might want s[i] + f[i] <= r[i] since only used tools need repair
    # and excess could be held... but there's no "hold" variable and holding is free.
    #
    # To handle holding properly we'd need inventory variables, but the standard
    # formulation for this classic problem assumes all tools in circulation are repaired.
    # Let's add: s[i] + f[i] <= avail[i], and also enforce that tools sent to repair
    # don't exceed what's available.

    # We'll track availability explicitly
    avail = {}
    for i in range(n):
        expr = x[i]
        if i - p >= 0:
            expr = expr + s[i - p]
        if i - q >= 0:
            expr = expr + f[i - q]
        avail[i] = expr

    for i in range(n):
        # Cannot send more tools to repair than are available
        model.addConstr(s[i] + f[i] <= avail[i], name=f"repair_cap_{i}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}