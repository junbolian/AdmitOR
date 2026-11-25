import gurobipy as gp
from gurobipy import GRB

def solve(params):
    supply = params["supply"]      # shape [4][2]
    demand = params["demand"]      # shape [5][2]
    cost = params["cost"]          # shape [4][5][2]
    capacity = params["capacity"]  # shape [4][5]

    origins = range(4)
    destinations = range(5)
    products = range(2)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    x = model.addVars(origins, destinations, products, lb=0.0, name="x")

    model.setObjective(
        gp.quicksum(
            cost[i][j][k] * x[i, j, k]
            for i in origins
            for j in destinations
            for k in products
        ),
        GRB.MINIMIZE
    )

    # Supply constraints: all supply must be fully used
    for i in origins:
        for k in products:
            model.addConstr(
                gp.quicksum(x[i, j, k] for j in destinations) == supply[i][k],
                name=f"supply_{i}_{k}"
            )

    # Demand constraints: all demand must be fully satisfied
    for j in destinations:
        for k in products:
            model.addConstr(
                gp.quicksum(x[i, j, k] for i in origins) == demand[j][k],
                name=f"demand_{j}_{k}"
            )

    # Capacity constraints: total units per origin-destination pair
    for i in origins:
        for j in destinations:
            model.addConstr(
                gp.quicksum(x[i, j, k] for k in products) <= capacity[i][j],
                name=f"capacity_{i}_{j}"
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