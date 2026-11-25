import gurobipy as gp
from gurobipy import GRB

def solve(params):
    investor_rankings = params["investor_rankings"]
    founder_rankings = params["founder_rankings"]

    n = len(investor_rankings)

    # inv_rank[i][j] = rank of founder j for investor i (0-indexed)
    inv_rank = {}
    for i in range(n):
        inv_rank[i] = {}
        for k, j in enumerate(investor_rankings[i]):
            inv_rank[i][j] = k

    # fnd_rank[j][i] = rank of investor i for founder j (0-indexed)
    fnd_rank = {}
    for j in range(n):
        fnd_rank[j] = {}
        for k, i in enumerate(founder_rankings[j]):
            fnd_rank[j][i] = k

    model = gp.Model("stable_matching")
    model.setParam("OutputFlag", 0)

    x = model.addVars(n, n, vtype=GRB.BINARY, name="x")

    for i in range(n):
        model.addConstr(gp.quicksum(x[i, j] for j in range(n)) == 1, name=f"inv_{i}")

    for j in range(n):
        model.addConstr(gp.quicksum(x[i, j] for i in range(n)) == 1, name=f"fnd_{j}")

    # Stability: for every pair (i, j), forbid it being a blocking pair.
    # A blocking pair requires:
    #   - i is not matched to any founder they prefer over j
    #   - j is not matched to any investor they prefer over i
    # Constraint: (better founders for i already matched to i)
    #           + (better investors for j already matched to j)
    #           + x[i,j]  (they are already matched to each other)
    #           >= 1
    # This covers all cases: if matched together, x[i,j]=1 satisfies it.
    # If not matched, at least one must hold a preferred partner.

    for i in range(n):
        for j in range(n):
            better_founders_for_i = [jp for jp in range(n) if inv_rank[i][jp] < inv_rank[i][j]]
            better_investors_for_j = [ip for ip in range(n) if fnd_rank[j][ip] < fnd_rank[j][i]]

            lhs = (gp.quicksum(x[i, jp] for jp in better_founders_for_i) +
                   gp.quicksum(x[ip, j] for ip in better_investors_for_j) +
                   x[i, j])

            model.addConstr(lhs >= 1, name=f"stability_{i}_{j}")

    obj = gp.quicksum(
        (inv_rank[i][j] + fnd_rank[j][i]) * x[i, j]
        for i in range(n)
        for j in range(n)
    )
    model.setObjective(obj, GRB.MINIMIZE)

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"solver_status_{model.Status}"}