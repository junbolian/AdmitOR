import gurobipy as gp
from gurobipy import GRB

def solve(params):
    opening_cost = params["opening_cost"]    # list of 8 values
    transport_cost = params["transport_cost"] # 8x5 matrix
    demand = params["demand"]                 # list of 5 values
    capacity = params["capacity"]             # list of 8 values

    num_dc = 8
    num_stores = 5

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Binary variable: whether DC i is opened
    open_dc = model.addVars(num_dc, vtype=GRB.BINARY, name="open_dc")

    # Continuous variable: units shipped from DC i to store j
    ship = model.addVars(num_dc, num_stores, vtype=GRB.CONTINUOUS, lb=0.0, name="ship")

    # Objective: minimize opening costs + transportation costs
    model.setObjective(
        gp.quicksum(opening_cost[i] * open_dc[i] for i in range(num_dc)) +
        gp.quicksum(transport_cost[i][j] * ship[i, j] for i in range(num_dc) for j in range(num_stores)),
        GRB.MINIMIZE
    )

    # Demand constraints: each store's demand must be fully met
    for j in range(num_stores):
        model.addConstr(
            gp.quicksum(ship[i, j] for i in range(num_dc)) >= demand[j],
            name=f"demand_{j}"
        )

    # Capacity constraints: shipments from DC i cannot exceed its capacity (only if open)
    for i in range(num_dc):
        model.addConstr(
            gp.quicksum(ship[i, j] for j in range(num_stores)) <= capacity[i] * open_dc[i],
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