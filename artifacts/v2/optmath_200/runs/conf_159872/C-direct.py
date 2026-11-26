import gurobipy as gp
from gurobipy import GRB

def solve(params):
    supply = params["supply"]      # shape: (4 origins) x (2 products)
    demand = params["demand"]      # shape: (5 destinations) x (2 products)
    cost = params["cost"]          # shape: (4 origins) x (5 destinations) x (2 products)
    capacity = params["capacity"]  # shape: (4 origins) x (5 destinations)

    num_origins = 4
    num_destinations = 5
    num_products = 2

    origins = range(num_origins)
    destinations = range(num_destinations)
    products = range(num_products)

    model = gp.Model("multi_commodity_transport")
    model.setParam("OutputFlag", 0)

    # Decision variables: x[i, j, k] = units of product k from origin i to destination j
    x = model.addVars(
        origins, destinations, products,
        lb=0.0,
        vtype=GRB.CONTINUOUS,
        name="x"
    )

    # Objective: minimize total transportation cost
    model.setObjective(
        gp.quicksum(
            cost[i][j][k] * x[i, j, k]
            for i in origins
            for j in destinations
            for k in products
        ),
        GRB.MINIMIZE
    )

    # Supply constraints: total shipped from origin i for product k == supply[i][k]
    for i in origins:
        for k in products:
            model.addConstr(
                gp.quicksum(x[i, j, k] for j in destinations) == supply[i][k],
                name=f"supply_{i}_{k}"
            )

    # Demand constraints: total received at destination j for product k == demand[j][k]
    for j in destinations:
        for k in products:
            model.addConstr(
                gp.quicksum(x[i, j, k] for i in origins) == demand[j][k],
                name=f"demand_{j}_{k}"
            )

    # Capacity constraints: total units (both products) from origin i to destination j <= capacity[i][j]
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