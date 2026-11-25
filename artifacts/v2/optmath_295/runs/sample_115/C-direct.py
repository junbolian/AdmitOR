import gurobipy as gp
from gurobipy import GRB


def solve(params):
    supplies = params["supplies"]
    demands = params["demands"]
    costs = params["costs"]

    n_orig = len(supplies)
    n_dest = len(demands)

    model = gp.Model("transportation")
    model.Params.OutputFlag = 0

    x = model.addVars(n_orig, n_dest, lb=0.0, name="x")

    model.setObjective(
        gp.quicksum(costs[i][j] * x[i, j] for i in range(n_orig) for j in range(n_dest)),
        GRB.MINIMIZE,
    )

    for i in range(n_orig):
        model.addConstr(
            gp.quicksum(x[i, j] for j in range(n_dest)) == supplies[i],
            name=f"supply_{i}",
        )

    for j in range(n_dest):
        model.addConstr(
            gp.quicksum(x[i, j] for i in range(n_orig)) == demands[j],
            name=f"demand_{j}",
        )

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}

    reasons = {
        GRB.INFEASIBLE: "infeasible",
        GRB.INF_OR_UNBD: "infeasible_or_unbounded",
        GRB.UNBOUNDED: "unbounded",
        GRB.TIME_LIMIT: "time_limit",
    }
    return {"objective": None, "status": reasons.get(model.status, "not_optimal")}