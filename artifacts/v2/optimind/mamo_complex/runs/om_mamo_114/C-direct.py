import gurobipy as gp
from gurobipy import GRB

def solve(params):
    opening_cost = params["opening_cost"]   # dict or list, indexed by center 1..6
    transport_cost = params["transport_cost"]  # 6x8 matrix, rows=centers, cols=stores
    demand = params["demand"]               # indexed by store 1..8
    capacity = params["capacity"]           # indexed by center 1..6

    num_centers = 6
    num_stores = 8
    centers = range(num_centers)
    stores = range(num_stores)

    # Normalize indexing: support both 0-based lists and 1-based dicts
    def get_opening_cost(i):
        if isinstance(opening_cost, dict):
            return opening_cost.get(i + 1, opening_cost.get(i))
        return opening_cost[i]

    def get_transport_cost(i, j):
        row = transport_cost[i] if not isinstance(transport_cost, dict) else transport_cost.get(i + 1, transport_cost.get(i))
        if isinstance(row, dict):
            return row.get(j + 1, row.get(j))
        return row[j]

    def get_demand(j):
        if isinstance(demand, dict):
            return demand.get(j + 1, demand.get(j))
        return demand[j]

    def get_capacity(i):
        if isinstance(capacity, dict):
            return capacity.get(i + 1, capacity.get(i))
        return capacity[i]

    model = gp.Model("GlobalSupply_FLP")
    model.setParam("OutputFlag", 0)

    # Decision variables
    # y[i] = 1 if center i is opened
    y = model.addVars(num_centers, vtype=GRB.BINARY, name="y")
    # x[i,j] = units shipped from center i to store j
    x = model.addVars(num_centers, num_stores, vtype=GRB.CONTINUOUS, lb=0.0, name="x")

    # Objective: minimize opening costs + transportation costs
    model.setObjective(
        gp.quicksum(get_opening_cost(i) * y[i] for i in centers) +
        gp.quicksum(get_transport_cost(i, j) * x[i, j] for i in centers for j in stores),
        GRB.MINIMIZE
    )

    # Demand constraints: each store's demand must be fully met
    for j in stores:
        model.addConstr(
            gp.quicksum(x[i, j] for i in centers) == get_demand(j),
            name=f"demand_{j}"
        )

    # Capacity constraints: shipments from center i cannot exceed its capacity if opened
    for i in centers:
        model.addConstr(
            gp.quicksum(x[i, j] for j in stores) <= get_capacity(i) * y[i],
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