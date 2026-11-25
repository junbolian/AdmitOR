import gurobipy as gp
from gurobipy import GRB

def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]
    limit = params["limit"]

    num_origins = len(supply)
    num_destinations = len(demand)

    model = gp.Model("transportation")
    model.setParam("OutputFlag", 0)

    x = model.addVars(num_origins, num_destinations, lb=0.0, name="x")

    # Objective: minimize total transportation cost
    model.setObjective(
        gp.quicksum(cost[i][j] * x[i, j] for i in range(num_origins) for j in range(num_destinations)),
        GRB.MINIMIZE
    )

    # Supply constraints
    for i in range(num_origins):
        model.addConstr(
            gp.quicksum(x[i, j] for j in range(num_destinations)) <= supply[i],
            name=f"supply_{i}"
        )

    # Demand constraints
    for j in range(num_destinations):
        model.addConstr(
            gp.quicksum(x[i, j] for i in range(num_origins)) >= demand[j],
            name=f"demand_{j}"
        )

    # Capacity limits
    for i in range(num_origins):
        for j in range(num_destinations):
            model.addConstr(x[i, j] <= limit[i][j], name=f"limit_{i}_{j}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}