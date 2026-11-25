import gurobipy as gp
from gurobipy import GRB

def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]
    capacity = params["capacity"]

    num_origins = len(supply)
    num_destinations = len(demand)

    model = gp.Model("transportation")
    model.setParam("OutputFlag", 0)

    # Decision variables
    x = {}
    for i in range(num_origins):
        for j in range(num_destinations):
            ub = capacity[i][j] if capacity[i][j] is not None else GRB.INFINITY
            x[i, j] = model.addVar(lb=0.0, ub=ub, obj=cost[i][j], name=f"x_{i}_{j}")

    model.ModelSense = GRB.MINIMIZE

    # Supply constraints (equality: fully utilized)
    for i in range(num_origins):
        model.addConstr(
            gp.quicksum(x[i, j] for j in range(num_destinations)) == supply[i],
            name=f"supply_{i}"
        )

    # Demand constraints (equality: exactly met)
    for j in range(num_destinations):
        model.addConstr(
            gp.quicksum(x[i, j] for i in range(num_origins)) == demand[j],
            name=f"demand_{j}"
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