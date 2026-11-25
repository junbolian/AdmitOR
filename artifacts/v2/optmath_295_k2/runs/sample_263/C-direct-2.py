import gurobipy as gp
from gurobipy import GRB

def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]
    capacity = params["capacity"]

    n_origins = 6
    n_destinations = 6

    model = gp.Model("transportation")
    model.setParam("OutputFlag", 0)

    x = model.addVars(n_origins, n_destinations, lb=0.0, name="x")

    # Capacity constraints
    for i in range(n_origins):
        for j in range(n_destinations):
            model.addConstr(x[i, j] <= capacity[i][j], name=f"cap_{i}_{j}")

    # Supply constraints (equality: fully utilize supply)
    for i in range(n_origins):
        model.addConstr(
            gp.quicksum(x[i, j] for j in range(n_destinations)) == supply[i],
            name=f"supply_{i}"
        )

    # Demand constraints (equality: fully satisfy demand)
    for j in range(n_destinations):
        model.addConstr(
            gp.quicksum(x[i, j] for i in range(n_origins)) == demand[j],
            name=f"demand_{j}"
        )

    # Objective: minimize total transportation cost
    model.setObjective(
        gp.quicksum(cost[i][j] * x[i, j] for i in range(n_origins) for j in range(n_destinations)),
        GRB.MINIMIZE
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