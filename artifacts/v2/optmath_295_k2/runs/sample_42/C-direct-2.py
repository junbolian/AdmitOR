import gurobipy as gp
from gurobipy import GRB


def solve(params):
    cost = params["cost"]          # cost[i][j][p]
    supply = params["supply"]      # supply[i][p]
    demand = params["demand"]      # demand[j][p]
    capacity = params["capacity"]  # capacity[i][j]

    num_products = 2
    num_origins = 4
    num_destinations = 5

    products = range(num_products)
    origins = range(num_origins)
    destinations = range(num_destinations)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    x = model.addVars(products, origins, destinations, lb=0.0, name="x")

    model.setObjective(
        gp.quicksum(
            cost[i][j][p] * x[p, i, j]
            for p in products
            for i in origins
            for j in destinations
        ),
        GRB.MINIMIZE,
    )

    for i in origins:
        for p in products:
            model.addConstr(
                gp.quicksum(x[p, i, j] for j in destinations) == supply[i][p],
                name=f"supply_{i}_{p}",
            )

    for j in destinations:
        for p in products:
            model.addConstr(
                gp.quicksum(x[p, i, j] for i in origins) == demand[j][p],
                name=f"demand_{j}_{p}",
            )

    for i in origins:
        for j in destinations:
            model.addConstr(
                gp.quicksum(x[p, i, j] for p in products) <= capacity[i][j],
                name=f"capacity_{i}_{j}",
            )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver_status_{model.Status}"}