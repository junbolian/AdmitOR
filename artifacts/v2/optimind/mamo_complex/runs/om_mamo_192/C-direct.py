import gurobipy as gp
from gurobipy import GRB

def solve(params):
    opening_cost = params["opening_cost"]   # list of length 9
    transport_cost = params["transport_cost"]  # 9x6 matrix
    demand = params["demand"]               # list of length 6
    capacity = params["capacity"]           # list of length 9

    num_dc = len(opening_cost)
    num_stores = len(demand)

    model = gp.Model("GlobalSupply")
    model.setParam("OutputFlag", 0)

    # Decision variables
    # y[i] = 1 if DC i is opened
    y = model.addVars(num_dc, vtype=GRB.BINARY, name="y")
    # x[i][j] = units shipped from DC i to store j
    x = model.addVars(num_dc, num_stores, vtype=GRB.CONTINUOUS, lb=0.0, name="x")

    # Objective: minimize opening costs + transportation costs
    model.setObjective(
        gp.quicksum(opening_cost[i] * y[i] for i in range(num_dc)) +
        gp.quicksum(transport_cost[i][j] * x[i, j] for i in range(num_dc) for j in range(num_stores)),
        GRB.MINIMIZE
    )

    # Demand constraints: each store's demand must be fully met
    for j in range(num_stores):
        model.addConstr(
            gp.quicksum(x[i, j] for i in range(num_dc)) >= demand[j],
            name=f"demand_{j}"
        )

    # Capacity constraints: cannot ship more than capacity if DC is open; zero if closed
    for i in range(num_dc):
        model.addConstr(
            gp.quicksum(x[i, j] for j in range(num_stores)) <= capacity[i] * y[i],
            name=f"capacity_{i}"
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
        return {"objective": None, "status": f"solver_status_{status}"}