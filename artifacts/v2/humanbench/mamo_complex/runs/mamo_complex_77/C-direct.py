import gurobipy as gp
from gurobipy import GRB

def solve(params):
    opening_cost_raw = params["opening_cost"]
    transport_cost_raw = params["transport_cost"]
    demand_raw = params["demand"]
    capacity_raw = params["capacity"]

    centers = range(1, 8)
    stores = range(1, 8)

    # Normalize opening_cost to 1-indexed dict
    if isinstance(opening_cost_raw, dict):
        opening_cost = opening_cost_raw
    else:
        # list: could be 0-indexed (length 7) or 1-indexed (length 8)
        if len(opening_cost_raw) == 7:
            opening_cost = {i: opening_cost_raw[i - 1] for i in centers}
        else:
            opening_cost = {i: opening_cost_raw[i] for i in centers}

    # Normalize capacity to 1-indexed dict
    if isinstance(capacity_raw, dict):
        capacity = capacity_raw
    else:
        if len(capacity_raw) == 7:
            capacity = {i: capacity_raw[i - 1] for i in centers}
        else:
            capacity = {i: capacity_raw[i] for i in centers}

    # Normalize demand to 1-indexed dict
    if isinstance(demand_raw, dict):
        demand = demand_raw
    else:
        if len(demand_raw) == 7:
            demand = {j: demand_raw[j - 1] for j in stores}
        else:
            demand = {j: demand_raw[j] for j in stores}

    # Normalize transport_cost to 1-indexed dict of dicts
    # transport_cost_raw is a 7x7 matrix (list of lists or dict of dicts)
    if isinstance(transport_cost_raw, dict):
        # dict keyed by center index; values are dicts or lists keyed by store index
        transport_cost = {}
        for i in centers:
            row = transport_cost_raw[i] if i in transport_cost_raw else transport_cost_raw[i - 1]
            if isinstance(row, dict):
                transport_cost[i] = row
            else:
                if len(row) == 7:
                    transport_cost[i] = {j: row[j - 1] for j in stores}
                else:
                    transport_cost[i] = {j: row[j] for j in stores}
    else:
        # list of lists
        transport_cost = {}
        if len(transport_cost_raw) == 7:
            for idx, i in enumerate(centers):
                row = transport_cost_raw[idx]
                if len(row) == 7:
                    transport_cost[i] = {j: row[j - 1] for j in stores}
                else:
                    transport_cost[i] = {j: row[j] for j in stores}
        else:
            for i in centers:
                row = transport_cost_raw[i]
                if len(row) == 7:
                    transport_cost[i] = {j: row[j - 1] for j in stores}
                else:
                    transport_cost[i] = {j: row[j] for j in stores}

    model = gp.Model("WareCo_distribution")
    model.setParam("OutputFlag", 0)

    # Binary variable: whether center i is opened
    y = model.addVars(centers, vtype=GRB.BINARY, name="y")

    # Continuous variable: units shipped from center i to store j
    x = model.addVars(centers, stores, vtype=GRB.CONTINUOUS, lb=0.0, name="x")

    # Objective: minimize opening costs + transportation costs
    model.setObjective(
        gp.quicksum(opening_cost[i] * y[i] for i in centers) +
        gp.quicksum(transport_cost[i][j] * x[i, j] for i in centers for j in stores),
        GRB.MINIMIZE
    )

    # Demand satisfaction: each store's demand must be fully met
    for j in stores:
        model.addConstr(
            gp.quicksum(x[i, j] for i in centers) == demand[j],
            name=f"demand_{j}"
        )

    # Capacity constraints: shipments from center i cannot exceed its capacity if opened
    for i in centers:
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