import gurobipy as gp
from gurobipy import GRB

def solve(params):
    opening_cost = params["opening_cost"]   # list of length 7
    transport_cost = params["transport_cost"]  # 7x6 nested list
    demand = params["demand"]               # list of length 6
    capacity = params["capacity"]           # list of length 7

    num_dc = 7
    num_stores = 6
    dcs = range(num_dc)
    stores = range(num_stores)

    model = gp.Model("supply_chain")
    model.setParam("OutputFlag", 0)

    # Binary variable: open DC i
    y = model.addVars(dcs, vtype=GRB.BINARY, name="open")

    # Continuous variable: units shipped from DC i to store j
    x = model.addVars(dcs, stores, vtype=GRB.CONTINUOUS, lb=0.0, name="ship")

    # Objective: minimize opening costs + transportation costs
    model.setObjective(
        gp.quicksum(opening_cost[i] * y[i] for i in dcs) +
        gp.quicksum(transport_cost[i][j] * x[i, j] for i in dcs for j in stores),
        GRB.MINIMIZE
    )

    # Demand constraints: each store's demand must be fully met
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

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}