import gurobipy as gp
from gurobipy import GRB

def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]
    arc_capacity = params["arc_capacity"]

    n_origins = 8
    n_destinations = 8

    # Determine uniform base capacity: largest individual supply
    max_supply = max(supply[i] for i in range(n_origins))

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Decision variables: flow[i][j] = units shipped from origin i to destination j
    flow = [[
        model.addVar(lb=0.0, name=f"flow_{i}_{j}")
        for j in range(n_destinations)]
        for i in range(n_origins)]

    # Supply constraints: each origin ships exactly its supply
    for i in range(n_origins):
        model.addConstr(
            gp.quicksum(flow[i][j] for j in range(n_destinations)) == supply[i],
            name=f"supply_{i}"
        )

    # Demand constraints: each destination receives exactly its demand
    for j in range(n_destinations):
        model.addConstr(
            gp.quicksum(flow[i][j] for i in range(n_origins)) == demand[j],
            name=f"demand_{j}"
        )

    # Arc capacity constraints
    for i in range(n_origins):
        for j in range(n_destinations):
            # Use explicit value from arc_capacity if provided, else uniform base
            cap = arc_capacity[i][j] if arc_capacity[i][j] is not None else max_supply
            model.addConstr(flow[i][j] <= cap, name=f"cap_{i}_{j}")

    # Objective: minimize total transportation cost
    model.setObjective(
        gp.quicksum(cost[i][j] * flow[i][j]
                    for i in range(n_origins)
                    for j in range(n_destinations)),
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
        return {"objective": None, "status": f"gurobi_status_{status}"}