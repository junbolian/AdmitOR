import gurobipy as gp
from gurobipy import GRB

def solve(params):
    opening_cost = params["opening_cost"]   # list of length 9
    transport_cost = params["transport_cost"]  # 9x5 list of lists
    demand = params["demand"]               # list of length 5
    capacity = params["capacity"]           # list of length 9

    num_dc = len(opening_cost)
    num_store = len(demand)

    model = gp.Model("GlobalSupply")
    model.setParam("OutputFlag", 0)

    # Binary variable: whether distribution center i is opened
    open_dc = model.addVars(num_dc, vtype=GRB.BINARY, name="open")

    # Continuous variable: units shipped from dc i to store j
    ship = model.addVars(num_dc, num_store, vtype=GRB.CONTINUOUS, lb=0.0, name="ship")

    # Objective: minimize opening costs + transportation costs
    model.setObjective(
        gp.quicksum(opening_cost[i] * open_dc[i] for i in range(num_dc)) +
        gp.quicksum(transport_cost[i][j] * ship[i, j]
                    for i in range(num_dc) for j in range(num_store)),
        GRB.MINIMIZE
    )

    # Demand constraints: each store's demand must be fully met
    for j in range(num_store):
        model.addConstr(
            gp.quicksum(ship[i, j] for i in range(num_dc)) >= demand[j],
            name=f"demand_{j}"
        )

    # Capacity constraints: shipments from dc i cannot exceed its capacity if open,
    # and must be zero if not open
    for i in range(num_dc):
        model.addConstr(
            gp.quicksum(ship[i, j] for j in range(num_store)) <= capacity[i] * open_dc[i],
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