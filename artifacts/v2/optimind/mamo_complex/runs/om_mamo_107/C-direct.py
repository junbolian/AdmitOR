import gurobipy as gp
from gurobipy import GRB

def solve(params):
    opening_cost = params["opening_cost"]   # list of 7
    transport_cost = params["transport_cost"]  # list of 7 lists of 6
    demand = params["demand"]               # list of 6
    capacity = params["capacity"]           # list of 7

    n_dc = 7
    n_store = 6
    dcs = range(n_dc)
    stores = range(n_store)

    model = gp.Model("supply_chain")
    model.setParam("OutputFlag", 0)

    # Binary variable: open DC i
    y = model.addVars(dcs, vtype=GRB.BINARY, name="y")

    # Continuous variable: units shipped from DC i to store j
    x = model.addVars(dcs, stores, vtype=GRB.CONTINUOUS, lb=0.0, name="x")

    # Objective: minimize opening costs + transportation costs
    model.setObjective(
        gp.quicksum(opening_cost[i] * y[i] for i in dcs) +
        gp.quicksum(transport_cost[i][j] * x[i, j] for i in dcs for j in stores),
        GRB.MINIMIZE
    )

    # Demand constraints: each store's demand must be met
    for j in stores:
        model.addConstr(
            gp.quicksum(x[i, j] for i in dcs) >= demand[j],
            name=f"demand_{j}"
        )

    # Capacity constraints: DC i can only ship up to capacity[i] if opened
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