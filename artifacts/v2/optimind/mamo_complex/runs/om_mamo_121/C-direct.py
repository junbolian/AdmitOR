import gurobipy as gp
from gurobipy import GRB

def solve(params):
    initial_food = params["initial_food"]   # list of length 6, 1-indexed values at positions 0..5
    required_food = params["required_food"] # list of length 6
    transport_cost = params["transport_cost"] # 6x6 matrix, diagonal unused

    n = 6
    regions = range(n)

    model = gp.Model("food_transport")
    model.setParam("OutputFlag", 0)

    # x[i][j] = tons moved from region i to region j (i != j)
    x = {}
    for i in regions:
        for j in regions:
            if i != j:
                x[i, j] = model.addVar(lb=0.0, name=f"x_{i}_{j}")

    # Objective: minimize total transport cost
    model.setObjective(
        gp.quicksum(transport_cost[i][j] * x[i, j] for i in regions for j in regions if i != j),
        GRB.MINIMIZE
    )

    # Each region's supply constraint: initial + inflow >= required + outflow
    # Equivalently: net outflow <= surplus, where surplus = initial - required (can be negative)
    for i in regions:
        outflow = gp.quicksum(x[i, j] for j in regions if j != i)
        inflow  = gp.quicksum(x[j, i] for j in regions if j != i)
        # initial[i] + inflow >= required[i] + outflow
        model.addConstr(
            initial_food[i] + inflow >= required_food[i] + outflow,
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