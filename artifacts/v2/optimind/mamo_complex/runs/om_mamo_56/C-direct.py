import gurobipy as gp
from gurobipy import GRB

def solve(params):
    opening_cost = params["opening_cost"]
    transport_cost = params["transport_cost"]
    demand = params["demand"]
    capacity = params["capacity"]

    centers = range(1, 8)
    stores = range(1, 5)

    # Helper to access data that may be 0-indexed lists or 1-indexed dicts
    def get_opening(i):
        if isinstance(opening_cost, dict):
            return opening_cost[i]
        else:
            return opening_cost[i - 1]

    def get_transport(i, j):
        if isinstance(transport_cost, dict):
            row = transport_cost[i]
        else:
            row = transport_cost[i - 1]
        if isinstance(row, dict):
            return row[j]
        else:
            return row[j - 1]

    def get_demand(j):
        if isinstance(demand, dict):
            return demand[j]
        else:
            return demand[j - 1]

    def get_capacity(i):
        if isinstance(capacity, dict):
            return capacity[i]
        else:
            return capacity[i - 1]

    model = gp.Model("SupplyTek")
    model.setParam("OutputFlag", 0)

    open_var = model.addVars(centers, vtype=GRB.BINARY, name="open")
    ship = model.addVars(centers, stores, vtype=GRB.CONTINUOUS, lb=0.0, name="ship")

    model.setObjective(
        gp.quicksum(get_opening(i) * open_var[i] for i in centers)
        + gp.quicksum(get_transport(i, j) * ship[i, j] for i in centers for j in stores),
        GRB.MINIMIZE
    )

    for j in stores:
        model.addConstr(
            gp.quicksum(ship[i, j] for i in centers) == get_demand(j),
            name=f"demand_{j}"
        )

    for i in centers:
        model.addConstr(
            gp.quicksum(ship[i, j] for j in stores) <= get_capacity(i) * open_var[i],
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
        return {"objective": None, "status": f"solver_status_{model.Status}"}