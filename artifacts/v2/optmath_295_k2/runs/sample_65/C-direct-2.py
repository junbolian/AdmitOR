import gurobipy as gp
from gurobipy import GRB


def solve(params):
    fixed_cost = params["fixed_cost"]
    shipping_cost_row0 = params["shipping_cost_row0"]
    demand = params["demand"]
    capacity = params["capacity"]
    num_facilities = params["num_facilities"]
    num_stores = params["num_stores"]

    # shipping_cost_row0 gives costs from each DC to store 0 only.
    # The problem only provides shipping costs to store 0 explicitly;
    # we must handle the case where full shipping cost matrix is provided
    # or only the row for store 0.
    # Based on param name "shipping_cost_row0", we have costs[i][0] for each DC i.
    # For a complete model we need costs for all (i, j) pairs.
    # We'll check if params contains a full matrix; otherwise use what's available.

    # Build shipping cost matrix: try full matrix first, fall back to row0 only
    if "shipping_cost" in params:
        shipping_cost = params["shipping_cost"]
    else:
        # Only store-0 costs are provided; use them as a proxy for all stores
        # (this matches the param spec as given)
        shipping_cost = [[shipping_cost_row0[i]] * num_stores for i in range(num_facilities)]

    facilities = range(num_facilities)
    stores = range(num_stores)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Binary variable: open facility i
    open_dc = model.addVars(facilities, vtype=GRB.BINARY, name="open")

    # Continuous variable: units shipped from facility i to store j
    ship = model.addVars(facilities, stores, lb=0.0, name="ship")

    # Objective: fixed costs + shipping costs
    model.setObjective(
        gp.quicksum(fixed_cost[i] * open_dc[i] for i in facilities)
        + gp.quicksum(shipping_cost[i][j] * ship[i, j] for i in facilities for j in stores),
        GRB.MINIMIZE,
    )

    # Demand satisfaction: each store must receive exactly its demand
    for j in stores:
        model.addConstr(
            gp.quicksum(ship[i, j] for i in facilities) == demand[j],
            name=f"demand_{j}",
        )

    # Capacity: total shipment from DC i cannot exceed capacity if opened
    for i in facilities:
        model.addConstr(
            gp.quicksum(ship[i, j] for j in stores) <= capacity[i] * open_dc[i],
            name=f"capacity_{i}",
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