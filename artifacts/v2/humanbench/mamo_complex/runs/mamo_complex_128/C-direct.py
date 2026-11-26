import gurobipy as gp
from gurobipy import GRB

def solve(params):
    supply = params["supply"]  # list of 7 values, index 0..6 -> centers 1..7
    demand = params["demand"]  # list of 7 values
    cost_flat = params["cost"]  # row-major over ordered pairs (i,j), i!=j, centers 1..7

    n = 7
    centers = range(n)

    # Build cost dict from flat list: ordered pairs (i,j) i!=j
    cost = {}
    idx = 0
    for i in centers:
        for j in centers:
            if i != j:
                cost[(i, j)] = cost_flat[idx]
                idx += 1

    model = gp.Model("redistribution")
    model.setParam("OutputFlag", 0)

    # Decision variables: x[i,j] = units transferred from center i to center j
    x = model.addVars(
        [(i, j) for i in centers for j in centers if i != j],
        lb=0.0,
        vtype=GRB.CONTINUOUS,
        name="x"
    )

    # Objective: minimize total transfer cost
    model.setObjective(
        gp.quicksum(cost[(i, j)] * x[i, j] for i in centers for j in centers if i != j),
        GRB.MINIMIZE
    )

    # Flow balance: supply[i] + inflow[i] - outflow[i] >= demand[i]
    for i in centers:
        inflow = gp.quicksum(x[j, i] for j in centers if j != i)
        outflow = gp.quicksum(x[i, j] for j in centers if j != i)
        model.addConstr(
            supply[i] + inflow - outflow >= demand[i],
            name=f"balance_{i}"
        )

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{status}"}