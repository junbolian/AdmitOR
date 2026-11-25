import gurobipy as gp
from gurobipy import GRB

def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]
    capacity = params["capacity"]

    num_origins = 5
    num_destinations = 6

    model = gp.Model("transportation")
    model.Params.OutputFlag = 0

    x = model.addVars(num_origins, num_destinations, lb=0.0, name="x")

    # Capacity constraints
    for i in range(num_origins):
        for j in range(num_destinations):
            model.addConstr(x[i, j] <= capacity[i][j], name=f"cap_{i}_{j}")

    # Supply constraints (equality)
    for i in range(num_origins):
        model.addConstr(
            gp.quicksum(x[i, j] for j in range(num_destinations)) == supply[i],
            name=f"supply_{i}"
        )

    # Demand constraints (equality)
    for j in range(num_destinations):
        model.addConstr(
            gp.quicksum(x[i, j] for i in range(num_origins)) == demand[j],
            name=f"demand_{j}"
        )

    # Objective
    model.setObjective(
        gp.quicksum(cost[i][j] * x[i, j] for i in range(num_origins) for j in range(num_destinations)),
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