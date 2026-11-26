import gurobipy as gp
from gurobipy import GRB

def solve(params):
    supply = params["supply"]
    demand = params["demand"]

    hospitals = [1, 2, 3, 4]

    # Build cost matrix from params (no self-transfers)
    cost = {}
    for i in hospitals:
        for j in hospitals:
            if i != j:
                key = f"cost_{i}_{j}"
                cost[(i, j)] = params[key]

    model = gp.Model("hospital_supply_transfer")
    model.setParam("OutputFlag", 0)

    # Decision variables: x[i,j] = units transferred from hospital i to hospital j
    x = {}
    for i in hospitals:
        for j in hospitals:
            if i != j:
                x[(i, j)] = model.addVar(lb=0.0, vtype=GRB.CONTINUOUS, name=f"x_{i}_{j}")

    # Objective: minimize total transfer cost
    model.setObjective(
        gp.quicksum(cost[(i, j)] * x[(i, j)] for i in hospitals for j in hospitals if i != j),
        GRB.MINIMIZE
    )

    # Supply constraints: a hospital cannot send out more than its surplus
    # Net flow balance: supply[i] + inflow[i] - outflow[i] >= demand[i]
    for i in hospitals:
        inflow = gp.quicksum(x[(j, i)] for j in hospitals if j != i)
        outflow = gp.quicksum(x[(i, j)] for j in hospitals if j != i)
        # supply is a list indexed 0-based (H1 is index 0)
        model.addConstr(
            supply[i - 1] + inflow - outflow >= demand[i - 1],
            name=f"balance_{i}"
        )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}