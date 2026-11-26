import gurobipy as gp
from gurobipy import GRB

def solve(params):
    a = params["a"]  # cost of purchasing a new tool
    b = params["b"]  # cost of slow repair
    c = params["c"]  # cost of fast repair
    p = params["p"]  # slow repair duration in stages
    q = params["q"]  # fast repair duration in stages
    r = params["r"]  # tool requirements per stage (index 0 unused, stages 1..n)
    n = params["n"]  # number of planning stages

    model = gp.Model("tool_planning")
    model.setParam("OutputFlag", 0)

    # Decision variables:
    # buy[j]   = number of new tools purchased at start of stage j (integer >= 0)
    # slow[j]  = number of tools sent for slow repair after stage j
    # fast[j]  = number of tools sent for fast repair after stage j
    # inv[j]   = inventory of available (ready-to-use) tools at the start of stage j

    stages = range(1, n + 1)

    buy  = model.addVars(stages, vtype=GRB.INTEGER, lb=0, name="buy")
    slow = model.addVars(stages, vtype=GRB.INTEGER, lb=0, name="slow")
    fast = model.addVars(stages, vtype=GRB.INTEGER, lb=0, name="fast")
    inv  = model.addVars(stages, vtype=GRB.INTEGER, lb=0, name="inv")

    # Objective: minimize total cost
    model.setObjective(
        gp.quicksum(a * buy[j] for j in stages) +
        gp.quicksum(b * slow[j] for j in stages) +
        gp.quicksum(c * fast[j] for j in stages),
        GRB.MINIMIZE
    )

    # Constraints:

    # 1. Available tools at stage j must meet requirement r[j]
    for j in stages:
        model.addConstr(inv[j] >= r[j], name=f"demand_{j}")

    # 2. Tools used in stage j = r[j], must all be sent for repair (or discarded)
    #    Total repaired = slow[j] + fast[j] <= r[j]
    #    (tools not repaired are simply discarded — no cost or benefit)
    for j in stages:
        model.addConstr(slow[j] + fast[j] <= r[j], name=f"repair_cap_{j}")

    # 3. Inventory balance: inventory at stage j+1 comes from:
    #    - leftover inventory not used in stage j: inv[j] - r[j]
    #    - new purchases at start of stage j+1: buy[j+1]
    #    - tools returned from slow repair sent after stage j-p: slow[j-p] if j-p >= 1
    #    - tools returned from fast repair sent after stage j-q: fast[j-q] if j-q >= 1
    for j in stages:
        if j < n:
            next_j = j + 1
            returned_slow = slow[j - p] if (j - p) >= 1 else 0
            returned_fast = fast[j - q] if (j - q) >= 1 else 0
            model.addConstr(
                inv[next_j] == inv[j] - r[j] + buy[next_j] + returned_slow + returned_fast,
                name=f"balance_{j}"
            )

    # 4. Initial inventory at stage 1: only new purchases contribute
    #    (no prior repairs available before stage 1)
    model.addConstr(inv[1] == buy[1], name="init_inv")

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver_status_{status}"}