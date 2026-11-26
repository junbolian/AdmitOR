import gurobipy as gp
from gurobipy import GRB

def solve(params):
    opening_cost = params["opening_cost"]   # list of length 7
    transport_cost = params["transport_cost"]  # 7x5 matrix
    demand = params["demand"]               # list of length 5
    capacity = params["capacity"]           # list of length 7

    num_dc = len(opening_cost)
    num_stores = len(demand)

    model = gp.Model("supply_chain")
    model.setParam("OutputFlag", 0)

    # y[i] = 1 if DC i is opened
    y = model.addVars(num_dc, vtype=GRB.BINARY, name="y")

    # x[i, j] = units shipped from DC i to store j
    x = model.addVars(num_dc, num_stores, vtype=GRB.CONTINUOUS, lb=0.0, name="x")

    # Objective: minimize opening costs + transportation costs
    model.setObjective(
        gp.quicksum(opening_cost[i] * y[i] for i in range(num_dc)) +
        gp.quicksum(transport_cost[i][j] * x[i, j] for i in range(num_dc) for j in range(num_stores)),
        GRB.MINIMIZE
    )

    # Demand satisfaction: each store j must receive exactly its demand
    for j in range(num_stores):
        model.addConstr(
            gp.quicksum(x[i, j] for i in range(num_dc)) >= demand[j],
            name=f"demand_{j}"
        )

    # Capacity: total shipped from DC i cannot exceed its capacity (and only if opened)
    for i in range(num_dc):
        model.addConstr(
            gp.quicksum(x[i, j] for j in range(num_stores)) <= capacity[i] * y[i],
            name=f"capacity_{i}"
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