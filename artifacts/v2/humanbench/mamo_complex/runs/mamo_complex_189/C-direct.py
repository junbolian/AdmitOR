import gurobipy as gp
from gurobipy import GRB

def solve(params):
    opening_cost_raw = params["opening_cost"]
    transport_cost_raw = params["transport_cost"]
    demand_raw = params["demand"]
    capacity_raw = params["capacity"]

    num_centers = 7
    num_stores = 9

    centers = range(num_centers)   # 0..6
    stores = range(num_stores)     # 0..8

    # Normalize to 0-based lists regardless of whether input is list or 1-based dict
    def to_list_1d(data, n):
        if isinstance(data, dict):
            # Try 1-based keys first, then 0-based
            if 1 in data:
                return [data[k] for k in range(1, n + 1)]
            else:
                return [data[k] for k in range(n)]
        else:
            return list(data)

    def to_list_2d(data, n_rows, n_cols):
        if isinstance(data, dict):
            # dict of dicts
            row_keys = sorted(data.keys())
            result = []
            for rk in row_keys:
                row = data[rk]
                if isinstance(row, dict):
                    col_keys = sorted(row.keys())
                    result.append([row[ck] for ck in col_keys])
                else:
                    result.append(list(row))
            return result
        else:
            # list of lists (or list of dicts)
            result = []
            for row in data:
                if isinstance(row, dict):
                    col_keys = sorted(row.keys())
                    result.append([row[ck] for ck in col_keys])
                else:
                    result.append(list(row))
            return result

    opening_cost = to_list_1d(opening_cost_raw, num_centers)
    demand = to_list_1d(demand_raw, num_stores)
    capacity = to_list_1d(capacity_raw, num_centers)
    transport_cost = to_list_2d(transport_cost_raw, num_centers, num_stores)

    model = gp.Model("logisticorp")
    model.setParam("OutputFlag", 0)

    # y[i] = 1 if center i is opened
    y = {i: model.addVar(vtype=GRB.BINARY, name=f"y_{i}") for i in centers}

    # x[i,j] = units shipped from center i to store j
    x = {
        (i, j): model.addVar(lb=0.0, vtype=GRB.CONTINUOUS, name=f"x_{i}_{j}")
        for i in centers for j in stores
    }

    # Objective: minimize opening costs + transportation costs
    model.setObjective(
        gp.quicksum(opening_cost[i] * y[i] for i in centers) +
        gp.quicksum(transport_cost[i][j] * x[i, j] for i in centers for j in stores),
        GRB.MINIMIZE
    )

    # Demand constraints: each store's demand must be fully met
    for j in stores:
        model.addConstr(
            gp.quicksum(x[i, j] for i in centers) == demand[j],
            name=f"demand_{j}"
        )

    # Capacity constraints: shipments from center i cannot exceed its capacity (only if open)
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