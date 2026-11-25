import gurobipy as gp
from gurobipy import GRB

def solve(params):
    route_revenue = params["route_revenue"]
    airport_capacity = params["airport_capacity"]

    # Fixed route structure: 17 routes in the stated edge order
    edges = [
        (0, 7), (0, 8), (0, 9),
        (1, 5), (1, 9),
        (2, 3), (2, 9),
        (3, 4), (3, 6), (3, 9),
        (4, 5),
        (5, 6), (5, 9),
        (6, 9),
        (7, 8), (7, 9),
        (8, 9),
    ]

    num_routes = len(edges)  # 17
    num_airports = 10

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Binary variable: 1 if route i is selected
    x = model.addVars(num_routes, vtype=GRB.BINARY, name="x")

    # Objective: maximize total revenue
    model.setObjective(
        gp.quicksum(route_revenue[i] * x[i] for i in range(num_routes)),
        GRB.MAXIMIZE
    )

    # Capacity constraints: for each airport, sum of selected routes incident to it <= capacity
    for a in range(num_airports):
        incident = [i for i, (u, v) in enumerate(edges) if u == a or v == a]
        if incident:
            model.addConstr(
                gp.quicksum(x[i] for i in incident) <= airport_capacity[a],
                name=f"cap_{a}"
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