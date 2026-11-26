import gurobipy as gp
from gurobipy import GRB

def solve(params):
    opening_cost = params["opening_cost"]  # list of 4 floats
    transport_cost = params["transport_cost"]  # 4x4 list of floats
    demand = params["demand"]  # list of 4 floats
    capacity = params["capacity"]  # list of 4 floats

    num_centers = 4
    num_outlets = 4
    centers = range(num_centers)
    outlets = range(num_outlets)

    model = gp.Model("supply_co")
    model.setParam("OutputFlag", 0)

    # Binary variable: whether center i is opened
    open_var = model.addVars(centers, vtype=GRB.BINARY, name="open")

    # Continuous variable: units shipped from center i to outlet j
    ship = model.addVars(centers, outlets, vtype=GRB.CONTINUOUS, lb=0.0, name="ship")

    # Objective: minimize opening costs + transportation costs
    model.setObjective(
        gp.quicksum(opening_cost[i] * open_var[i] for i in centers) +
        gp.quicksum(transport_cost[i][j] * ship[i, j] for i in centers for j in outlets),
        GRB.MINIMIZE
    )

    # Demand satisfaction: each outlet j must receive at least its demand
    for j in outlets:
        model.addConstr(
            gp.quicksum(ship[i, j] for i in centers) >= demand[j],
            name=f"demand_{j}"
        )

    # Capacity: total shipped from center i cannot exceed its capacity (and only if opened)
    for i in centers:
        model.addConstr(
            gp.quicksum(ship[i, j] for j in outlets) <= capacity[i] * open_var[i],
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