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
    # The problem only provides column 0 of the full shipping cost matrix via params.
    # We use shipping_cost_row0[i] as the cost from DC i to store j for all j,
    # since no other per-(i,j) cost data is provided in params.
    # (The problem description lists costs only for store 0.)

    facilities = range(num_facilities)
    stores = range(num_stores)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Binary open/close decision for each facility
    open_dc = model.addVars(facilities, vtype=GRB.BINARY, name="open")

    # Continuous shipment from facility i to store j
    ship = model.addVars(facilities, stores, lb=0.0, name="ship")

    # Objective: fixed costs + variable shipping costs
    # Only store-0 costs are parameterized; use shipping_cost_row0[i] for all stores
    # since the params dict contains no other shipping cost data.
    model.setObjective(
        gp.quicksum(fixed_cost[i] * open_dc[i] for i in facilities)
        + gp.quicksum(
            shipping_cost_row0[i] * ship[i, j]
            for i in facilities
            for j in stores
        ),
        GRB.MINIMIZE,
    )

    # Demand satisfaction: each store must receive exactly its demand
    for j in stores:
        model.addConstr(
            gp.quicksum(ship[i, j] for i in facilities) == demand[j],
            name=f"demand_{j}",
        )

    # Capacity: total shipment from DC i cannot exceed capacity[i] * open_dc[i]
    for i in facilities:
        model.addConstr(
            gp.quicksum(ship[i, j] for j in stores) <= capacity[i] * open_dc[i],
            name=f"capacity_{i}",
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