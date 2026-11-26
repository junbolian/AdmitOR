import gurobipy as gp
from gurobipy import GRB

def solve(params):
    opening_cost = params["opening_cost"]
    transport_cost = params["transport_cost"]
    demand = params["demand"]
    capacity = params["capacity"]

    num_dc = 6
    num_stores = 9
    dcs = range(num_dc)
    stores = range(num_stores)

    model = gp.Model("GlobalSupply")
    model.setParam("OutputFlag", 0)

    # Decision variables
    # y[i] = 1 if DC i is opened
    y = model.addVars(dcs, vtype=GRB.BINARY, name="y")
    # x[i,j] = units shipped from DC i to store j
    x = model.addVars(dcs, stores, vtype=GRB.CONTINUOUS, lb=0.0, name="x")

    # Objective: minimize opening costs + transportation costs
    model.setObjective(
        gp.quicksum(opening_cost[i] * y[i] for i in dcs) +
        gp.quicksum(transport_cost[i][j] * x[i, j] for i in dcs for j in stores),
        GRB.MINIMIZE
    )

    # Demand satisfaction: each store's demand must be fully met
    for j in stores:
        model.addConstr(
            gp.quicksum(x[i, j] for i in dcs) == demand[j],
            name=f"demand_{j}"
        )

    # Capacity constraints: shipments from DC i cannot exceed its capacity (only if open)
    for i in dcs:
        model.addConstr(
            gp.quicksum(x[i, j] for j in stores) <= capacity[i] * y[i],
            name=f"capacity_{i}"
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