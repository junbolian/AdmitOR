import gurobipy as gp
from gurobipy import GRB

def solve(params):
    cost_matrix = params["cost_matrix"]
    supply = params["supply"]
    demand = params["demand"]

    n = 5
    regions = range(n)

    model = gp.Model("freight_car_relocation")
    model.setParam("OutputFlag", 0)

    # x[i][j] = number of cars moved from region i to region j
    x = [[None] * n for _ in regions]
    for i in regions:
        for j in regions:
            if i != j:
                x[i][j] = model.addVar(lb=0, vtype=GRB.CONTINUOUS, name=f"x_{i}_{j}")

    # Objective: minimize total transportation cost
    obj = gp.LinExpr()
    for i in regions:
        for j in regions:
            if i != j:
                obj += cost_matrix[i][j] * x[i][j]
    model.setObjective(obj, GRB.MINIMIZE)

    # Flow balance: for each region, net outflow = supply - demand
    # supply[i] + inflow[i] - outflow[i] >= demand[i]
    # equivalently: outflow[i] - inflow[i] <= supply[i] - demand[i]
    # But we want to allow surplus cars to stay, so:
    # supply[i] - sum_j(x[i][j]) + sum_j(x[j][i]) >= demand[i]
    for i in regions:
        outflow = gp.LinExpr()
        inflow = gp.LinExpr()
        for j in regions:
            if i != j:
                outflow += x[i][j]
                inflow += x[j][i]
        # Cars available after movement must meet demand
        model.addConstr(supply[i] - outflow + inflow >= demand[i], name=f"demand_{i}")
        # Cannot ship out more than available
        model.addConstr(outflow <= supply[i], name=f"supply_{i}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}