import gurobipy as gp
from gurobipy import GRB

def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost_matrix = params["cost_matrix"]

    n = len(supply)
    clinics = range(n)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # x[i][j] = units transferred from clinic i to clinic j
    x = [[None] * n for _ in clinics]
    for i in clinics:
        for j in clinics:
            if i != j:
                x[i][j] = model.addVar(lb=0.0, vtype=GRB.CONTINUOUS)

    # Objective: minimize total transfer cost
    obj = gp.LinExpr()
    for i in clinics:
        for j in clinics:
            if i != j:
                obj += cost_matrix[i][j] * x[i][j]
    model.setObjective(obj, GRB.MINIMIZE)

    # Flow balance: supply[i] + inflow[i] - outflow[i] >= demand[i]
    for i in clinics:
        inflow = gp.quicksum(x[j][i] for j in clinics if j != i)
        outflow = gp.quicksum(x[i][j] for j in clinics if j != i)
        model.addConstr(supply[i] + inflow - outflow >= demand[i])

    # Cannot send out more than available net supply (non-negativity of remaining stock)
    for i in clinics:
        outflow = gp.quicksum(x[i][j] for j in clinics if j != i)
        model.addConstr(outflow <= supply[i])

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}