import gurobipy as gp
from gurobipy import GRB

def solve(params):
    supply = params["supply"]  # supply[i][p]
    demand = params["demand"]  # demand[j][p]
    cost = params["cost"]      # cost[i][j][p]
    cap = params["cap"]        # cap[i][j]

    num_origins = len(supply)
    num_destinations = len(demand)
    num_products = len(supply[0])

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Decision variables: x[i][j][p] = units of product p shipped from origin i to destination j
    x = [
        [
            [
                model.addVar(lb=0.0, name=f"x_{i}_{j}_{p}")
                for p in range(num_products)
            ]
            for j in range(num_destinations)
        ]
        for i in range(num_origins)
    ]

    # Objective: minimize total transportation cost
    model.setObjective(
        gp.quicksum(
            cost[i][j][p] * x[i][j][p]
            for i in range(num_origins)
            for j in range(num_destinations)
            for p in range(num_products)
        ),
        GRB.MINIMIZE
    )

    # Supply constraints: total shipped from origin i for product p == supply[i][p]
    for i in range(num_origins):
        for p in range(num_products):
            model.addConstr(
                gp.quicksum(x[i][j][p] for j in range(num_destinations)) == supply[i][p],
                name=f"supply_{i}_{p}"
            )

    # Demand constraints: total received at destination j for product p == demand[j][p]
    for j in range(num_destinations):
        for p in range(num_products):
            model.addConstr(
                gp.quicksum(x[i][j][p] for i in range(num_origins)) == demand[j][p],
                name=f"demand_{j}_{p}"
            )

    # Capacity constraints: total units (all products) from origin i to destination j <= cap[i][j]
    for i in range(num_origins):
        for j in range(num_destinations):
            model.addConstr(
                gp.quicksum(x[i][j][p] for p in range(num_products)) <= cap[i][j],
                name=f"cap_{i}_{j}"
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