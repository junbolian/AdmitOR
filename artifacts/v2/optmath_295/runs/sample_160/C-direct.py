import gurobipy as gp
from gurobipy import GRB

def solve(params):
    fixed_cost_dc = params["fixed_cost_dc"]
    shipping_cost = params["shipping_cost"]
    store_demand = params["store_demand"]
    dc_capacity = params["dc_capacity"]

    n_dc = 7
    n_store = 8

    model = gp.Model("facility_location")
    model.setParam("OutputFlag", 0)

    # Binary: open DC i
    open_dc = model.addVars(n_dc, vtype=GRB.BINARY, name="open_dc")

    # Continuous: units shipped from DC i to store j
    ship = model.addVars(n_dc, n_store, vtype=GRB.CONTINUOUS, lb=0.0, name="ship")

    # Objective: fixed costs + shipping costs
    model.setObjective(
        gp.quicksum(fixed_cost_dc[i] * open_dc[i] for i in range(n_dc)) +
        gp.quicksum(shipping_cost[i][j] * ship[i, j] for i in range(n_dc) for j in range(n_store)),
        GRB.MINIMIZE
    )

    # Demand satisfaction: each store j must receive exactly its demand
    for j in range(n_store):
        model.addConstr(
            gp.quicksum(ship[i, j] for i in range(n_dc)) == store_demand[j],
            name=f"demand_{j}"
        )

    # Capacity: total shipped from DC i cannot exceed capacity if open
    for i in range(n_dc):
        model.addConstr(
            gp.quicksum(ship[i, j] for j in range(n_store)) <= dc_capacity[i] * open_dc[i],
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