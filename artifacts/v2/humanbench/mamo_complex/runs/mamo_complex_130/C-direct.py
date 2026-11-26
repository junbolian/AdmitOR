import gurobipy as gp
from gurobipy import GRB

def solve(params):
    stock = params["stock"]  # list of length n
    need = params["need"]    # list of length n
    cost = params["cost"]    # n x n matrix

    n = len(stock)
    regions = range(n)

    model = gp.Model("medical_supply_distribution")
    model.setParam("OutputFlag", 0)

    # x[i][j] = units transferred from region i to region j
    x = [[None] * n for _ in regions]
    for i in regions:
        for j in regions:
            if i != j:
                x[i][j] = model.addVar(lb=0.0, vtype=GRB.CONTINUOUS, name=f"x_{i}_{j}")

    # Objective: minimize total transfer cost
    obj = gp.LinExpr()
    for i in regions:
        for j in regions:
            if i != j:
                obj += cost[i][j] * x[i][j]
    model.setObjective(obj, GRB.MINIMIZE)

    # Supply constraints: outflow from region i cannot exceed surplus (stock - need if positive, else stock)
    # More precisely: stock[i] + inflow[i] - outflow[i] >= need[i]
    for i in regions:
        inflow = gp.LinExpr()
        outflow = gp.LinExpr()
        for j in regions:
            if j != i:
                inflow += x[j][i]
                outflow += x[i][j]
        model.addConstr(stock[i] + inflow - outflow >= need[i], name=f"balance_{i}")

    # Non-negativity already enforced by lb=0
    # Also ensure outflow doesn't exceed available stock plus inflow (implicit via balance)

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