import gurobipy as gp
from gurobipy import GRB

def solve(params):
    opening_costs = [
        params["opening_cost_center_1"],
        params["opening_cost_center_2"],
        params["opening_cost_center_3"],
        params["opening_cost_center_4"],
        params["opening_cost_center_5"],
        params["opening_cost_center_6"],
        params["opening_cost_center_7"],
    ]
    transport_cost = params["transportation_cost_matrix"]  # 7 x 9
    demand = params["store_demand"]          # length 9
    capacity = params["center_capacity"]     # length 7

    num_centers = 7
    num_stores = 9

    centers = range(num_centers)
    stores = range(num_stores)

    model = gp.Model("supply_chain")
    model.setParam("OutputFlag", 0)

    # Binary variable: whether to open center i
    open_center = model.addVars(centers, vtype=GRB.BINARY, name="open")

    # Continuous variable: units shipped from center i to store j
    ship = model.addVars(centers, stores, vtype=GRB.CONTINUOUS, lb=0.0, name="ship")

    # Objective: minimize opening costs + transportation costs
    obj = (
        gp.quicksum(opening_costs[i] * open_center[i] for i in centers)
        + gp.quicksum(transport_cost[i][j] * ship[i, j] for i in centers for j in stores)
    )
    model.setObjective(obj, GRB.MINIMIZE)

    # Demand constraints: each store's demand must be fully met
    for j in stores:
        model.addConstr(
            gp.quicksum(ship[i, j] for i in centers) >= demand[j],
            name=f"demand_{j}"
        )

    # Capacity constraints: total shipped from center i <= capacity[i] * open_center[i]
    for i in centers:
        model.addConstr(
            gp.quicksum(ship[i, j] for j in stores) <= capacity[i] * open_center[i],
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