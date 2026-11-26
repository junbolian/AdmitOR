import gurobipy as gp
from gurobipy import GRB

def solve(params):
    opening_cost = params["opening_cost"]
    transport_cost = params["transport_cost"]
    demand = params["demand"]
    capacity = params["capacity"]

    n_dc = len(opening_cost)
    n_stores = len(demand)

    model = gp.Model("wareco_distribution")
    model.setParam("OutputFlag", 0)

    # Binary variable: open DC i
    open_dc = model.addVars(n_dc, vtype=GRB.BINARY, name="open")

    # Continuous variable: units shipped from DC i to store j
    ship = model.addVars(n_dc, n_stores, lb=0.0, name="ship")

    # Objective: minimize opening costs + transportation costs
    model.setObjective(
        gp.quicksum(opening_cost[i] * open_dc[i] for i in range(n_dc)) +
        gp.quicksum(transport_cost[i][j] * ship[i, j] for i in range(n_dc) for j in range(n_stores)),
        GRB.MINIMIZE
    )

    # Demand satisfaction: each store's demand must be met
    for j in range(n_stores):
        model.addConstr(
            gp.quicksum(ship[i, j] for i in range(n_dc)) >= demand[j],
            name=f"demand_{j}"
        )

    # Capacity constraints: DC i can only ship if open, up to its capacity
    for i in range(n_dc):
        model.addConstr(
            gp.quicksum(ship[i, j] for j in range(n_stores)) <= capacity[i] * open_dc[i],
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