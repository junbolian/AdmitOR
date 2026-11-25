import gurobipy as gp
from gurobipy import GRB


def solve(params):
    investor_rankings = params["investor_rankings"]
    founder_rankings = params["founder_rankings"]

    n = len(investor_rankings)

    inv_rank = [[0] * n for _ in range(n)]
    for i in range(n):
        for pos, j in enumerate(investor_rankings[i]):
            inv_rank[i][j] = pos

    fou_rank = [[0] * n for _ in range(n)]
    for j in range(n):
        for pos, i in enumerate(founder_rankings[j]):
            fou_rank[j][i] = pos

    model = gp.Model("stable_marriage_syndication")
    model.Params.OutputFlag = 0

    x = {}
    for i in range(n):
        for j in range(n):
            x[i, j] = model.addVar(vtype=GRB.BINARY, name=f"x_{i}_{j}")

    for i in range(n):
        model.addConstr(gp.quicksum(x[i, j] for j in range(n)) == 1, name=f"inv_match_{i}")

    for j in range(n):
        model.addConstr(gp.quicksum(x[i, j] for i in range(n)) == 1, name=f"fou_match_{j}")

    for i in range(n):
        for j in range(n):
            less_pref_inv = gp.quicksum(
                x[i, k] for k in range(n) if inv_rank[i][k] > inv_rank[i][j]
            )
            less_pref_fou = gp.quicksum(
                x[k, j] for k in range(n) if fou_rank[j][k] > fou_rank[j][i]
            )
            model.addConstr(
                less_pref_inv + less_pref_fou <= 1,
                name=f"stability_{i}_{j}",
            )

    model.setObjective(
        gp.quicksum(
            (inv_rank[i][j] + fou_rank[j][i]) * x[i, j]
            for i in range(n)
            for j in range(n)
        ),
        GRB.MINIMIZE,
    )

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}

    return {"objective": None, "status": "infeasible"}