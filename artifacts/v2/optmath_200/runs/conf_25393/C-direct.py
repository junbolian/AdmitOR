import gurobipy as gp
from gurobipy import GRB


def solve(params):
    n = 8
    nd = params["net_demand"]
    if isinstance(nd, dict):
        demand = [nd[i] if i in nd else nd[str(i)] for i in range(n)]
    else:
        demand = list(nd)

    arcs = [(i, j) for i in range(n) for j in range(n) if i != j]
    cost = {(i, j): params[f"cost_{i}_to_{j}"] for (i, j) in arcs}
    cap = {(i, j): params[f"cap_{i}_to_{j}"] for (i, j) in arcs}

    model = gp.Model("min_cost_flow")
    model.Params.OutputFlag = 0

    x = {}
    for (i, j) in arcs:
        x[i, j] = model.addVar(lb=0.0, ub=cap[i, j], name=f"x_{i}_{j}")

    model.setObjective(gp.quicksum(cost[a] * x[a] for a in arcs), GRB.MINIMIZE)

    for k in range(n):
        inflow = gp.quicksum(x[i, k] for i in range(n) if i != k)
        outflow = gp.quicksum(x[k, j] for j in range(n) if j != k)
        model.addConstr(inflow - outflow == demand[k], name=f"balance_{k}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    if model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    if model.Status == GRB.INF_OR_UNBD:
        return {"objective": None, "status": "infeasible_or_unbounded"}
    return {"objective": None, "status": f"status_{model.Status}"}