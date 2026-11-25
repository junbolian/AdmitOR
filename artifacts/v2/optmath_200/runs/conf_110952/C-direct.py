import gurobipy as gp
from gurobipy import GRB

def solve(params):
    supply = params["supply"]  # shape: 6 x 2
    demand = params["demand"]  # shape: 5 x 2
    cost = params["cost"]      # shape: 6 x 5 x 2
    limit = params["limit"]    # shape: 6 x 5

    num_origins = 6
    num_destinations = 5
    num_products = 2

    model = gp.Model("transportation")
    model.setParam("OutputFlag", 0)

    # Decision variables: x[i, j, p] = units of product p shipped from origin i to destination j
    x = {}
    for i in range(num_origins):
        for j in range(num_destinations):
            for p in range(num_products):
                x[i, j, p] = model.addVar(lb=0.0, vtype=GRB.CONTINUOUS, name=f"x_{i}_{j}_{p}")

    # Objective: minimize total shipping cost
    model.setObjective(
        gp.quicksum(cost[i][j][p] * x[i, j, p]
                    for i in range(num_origins)
                    for j in range(num_destinations)
                    for p in range(num_products)),
        GRB.MINIMIZE
    )

    # Supply constraints: total shipped from origin i for product p <= supply[i][p]
    for i in range(num_origins):
        for p in range(num_products):
            model.addConstr(
                gp.quicksum(x[i, j, p] for j in range(num_destinations)) == supply[i][p],
                name=f"supply_{i}_{p}"
            )

    # Demand constraints: total received at destination j for product p >= demand[j][p]
    for j in range(num_destinations):
        for p in range(num_products):
            model.addConstr(
                gp.quicksum(x[i, j, p] for i in range(num_origins)) == demand[j][p],
                name=f"demand_{j}_{p}"
            )

    # Capacity constraints: total units (both products) on each origin-destination pair <= limit[i][j]
    for i in range(num_origins):
        for j in range(num_destinations):
            model.addConstr(
                gp.quicksum(x[i, j, p] for p in range(num_products)) <= limit[i][j],
                name=f"limit_{i}_{j}"
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