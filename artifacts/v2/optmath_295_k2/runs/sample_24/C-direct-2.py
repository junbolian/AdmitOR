import gurobipy as gp
from gurobipy import GRB

def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]
    capacity = params["capacity"]

    n_origins = 6
    n_destinations = 6
    origins = range(n_origins)
    destinations = range(n_destinations)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    x = model.addVars(origins, destinations, lb=0.0, name="x")

    # Capacity constraints
    for i in origins:
        for j in destinations:
            model.addConstr(x[i, j] <= capacity[i][j], name=f"cap_{i}_{j}")

    # Supply constraints (equality: all supply must be used)
    for i in origins:
        model.addConstr(gp.quicksum(x[i, j] for j in destinations) == supply[i], name=f"supply_{i}")

    # Demand constraints (equality: all demand must be met)
    for j in destinations:
        model.addConstr(gp.quicksum(x[i, j] for i in origins) == demand[j], name=f"demand_{j}")

    # Objective: minimize total transportation cost
    model.setObjective(
        gp.quicksum(cost[i][j] * x[i, j] for i in origins for j in destinations),
        GRB.MINIMIZE
    )

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver_status_{status}"}