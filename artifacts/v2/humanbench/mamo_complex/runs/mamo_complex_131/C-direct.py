import gurobipy as gp
from gurobipy import GRB

def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    transport_cost = params["transport_cost"]

    n = len(supply)
    clinics = range(n)

    model = gp.Model("clinic_supply")
    model.setParam("OutputFlag", 0)

    # x[i][j] = units transferred from clinic i to clinic j
    x = [[None] * n for _ in clinics]
    for i in clinics:
        for j in clinics:
            if i != j:
                x[i][j] = model.addVar(lb=0.0, name=f"x_{i}_{j}")

    # Objective: minimize total transport cost
    obj = gp.LinExpr()
    for i in clinics:
        for j in clinics:
            if i != j:
                obj += transport_cost[i][j] * x[i][j]
    model.setObjective(obj, GRB.MINIMIZE)

    # Flow balance: supply[i] + inflow[i] - outflow[i] >= demand[i]
    # Surplus supply can remain at the originating clinic (no forced disposal needed)
    for i in clinics:
        inflow = gp.quicksum(x[j][i] for j in clinics if j != i)
        outflow = gp.quicksum(x[i][j] for j in clinics if j != i)
        model.addConstr(supply[i] + inflow - outflow >= demand[i], name=f"balance_{i}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}