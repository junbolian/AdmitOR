import gurobipy as gp
from gurobipy import GRB

def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    transfer_cost = params["transfer_cost"]
    num_centers = params["num_centers"]

    n = num_centers
    centers = range(n)

    model = gp.Model("supply_redistribution")
    model.setParam("OutputFlag", 0)

    # Decision variables: x[i][j] = units transferred from center i to center j
    x = {}
    for i in centers:
        for j in centers:
            if i != j:
                x[i, j] = model.addVar(lb=0.0, vtype=GRB.CONTINUOUS, name=f"x_{i}_{j}")

    # Objective: minimize total transfer cost
    model.setObjective(
        gp.quicksum(transfer_cost[i][j] * x[i, j] for i in centers for j in centers if i != j),
        GRB.MINIMIZE
    )

    # Flow balance constraints: for each center, supply + inflow - outflow >= demand
    for i in centers:
        inflow = gp.quicksum(x[j, i] for j in centers if j != i)
        outflow = gp.quicksum(x[i, j] for j in centers if j != i)
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