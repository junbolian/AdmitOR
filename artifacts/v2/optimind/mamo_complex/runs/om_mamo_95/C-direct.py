import gurobipy as gp
from gurobipy import GRB

def solve(params):
    supply = params["supply"]
    demand = params["demand"]

    # Build cost dict for all (i,j) pairs where i != j, 1-indexed
    n = 6
    cost = {}
    for i in range(1, n + 1):
        for j in range(1, n + 1):
            if i != j:
                key = f"cost_{i}_{j}"
                cost[(i, j)] = params[key]

    model = gp.Model("warehouse_rebalancing")
    model.setParam("OutputFlag", 0)

    # Decision variables: x[i,j] = units shipped from warehouse i to warehouse j
    x = {}
    for i in range(1, n + 1):
        for j in range(1, n + 1):
            if i != j:
                x[(i, j)] = model.addVar(lb=0.0, vtype=GRB.CONTINUOUS, name=f"x_{i}_{j}")

    # Objective: minimize total transport cost
    model.setObjective(
        gp.quicksum(cost[(i, j)] * x[(i, j)] for i in range(1, n + 1) for j in range(1, n + 1) if i != j),
        GRB.MINIMIZE
    )

    # Flow balance constraints:
    # supply[i] + inflow[i] - outflow[i] >= demand[i]
    # i.e., net shipment out = supply[i] - demand[i]
    for i in range(1, n + 1):
        inflow = gp.quicksum(x[(j, i)] for j in range(1, n + 1) if j != i)
        outflow = gp.quicksum(x[(i, j)] for j in range(1, n + 1) if j != i)
        # supply[i-1] + inflow - outflow >= demand[i-1]
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