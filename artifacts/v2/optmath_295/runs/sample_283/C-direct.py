import gurobipy as gp
from gurobipy import GRB

def solve(params):
    revenue = params["revenue"]
    demand_limit = params["demand_limit"]
    route_capacity = params["route_capacity"]

    num_packages = 23
    num_routes = 15

    # Route membership: which packages belong to each route
    route_packages = [
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 10, 11, 12, 15, 16, 17, 18, 19, 20, 21],
        [1, 2, 4, 5, 6, 8, 9, 10, 11, 12, 14, 15, 16, 17, 18, 19, 22],
        [2, 3, 4, 8, 9, 11, 12, 13, 15, 17, 18, 20, 21],
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 19, 20, 21, 22],
        [1, 3, 4, 5, 7, 8, 9, 10, 13, 14, 15, 17, 18, 20, 21, 22],
        [0, 1, 2, 4, 5, 6, 8, 9, 10, 11, 12, 13, 16, 17, 18, 20, 21, 22],
        [0, 1, 2, 3, 4, 5, 6, 8, 9, 13, 15, 16, 17, 18, 19, 21, 22],
        [0, 1, 2, 5, 7, 8, 10, 12, 14, 16, 19, 20, 21, 22],
        [2, 3, 4, 5, 6, 7, 9, 10, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22],
        [0, 1, 5, 6, 7, 8, 9, 10, 13, 14, 15, 17, 18, 19, 20],
        [0, 1, 2, 3, 4, 6, 8, 9, 10, 12, 13, 14, 15, 16, 17, 22],
        [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 18, 19, 20, 21],
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22],
        [0, 1, 2, 6, 7, 8, 10, 11, 13, 15, 16, 17, 18, 19, 20, 22],
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 17, 18, 19, 20, 21, 22],
    ]

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Decision variables: integer units sold for each package
    x = model.addVars(num_packages, vtype=GRB.INTEGER, lb=0, name="x")

    # Demand constraints
    for p in range(num_packages):
        model.addConstr(x[p] <= demand_limit[p], name=f"demand_{p}")

    # Route capacity constraints
    for r in range(num_routes):
        model.addConstr(
            gp.quicksum(x[p] for p in route_packages[r]) <= route_capacity[r],
            name=f"route_{r}"
        )

    # Objective: maximize total revenue
    model.setObjective(
        gp.quicksum(revenue[p] * x[p] for p in range(num_packages)),
        GRB.MAXIMIZE
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