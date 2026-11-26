import gurobipy as gp
from gurobipy import GRB

def solve(params):
    opening_cost = params["opening_cost"]
    transport_cost = params["transport_cost"]
    demand = params["demand"]
    capacity = params["capacity"]

    DCs = range(5)
    stores = range(7)

    model = gp.Model("distribution_dynamics")
    model.setParam("OutputFlag", 0)

    # y[i] = 1 if DC i is opened
    y = {i: model.addVar(vtype=GRB.BINARY, name=f"y_{i}") for i in DCs}
    # x[i,j] = units shipped from DC i to store j
    x = {(i, j): model.addVar(lb=0.0, name=f"x_{i}_{j}") for i in DCs for j in stores}

    # Objective: minimize opening costs + transportation costs
    model.setObjective(
        gp.quicksum(opening_cost[i] * y[i] for i in DCs) +
        gp.quicksum(transport_cost[i][j] * x[i, j] for i in DCs for j in stores),
        GRB.MINIMIZE
    )

    # Demand constraints: each store's demand must be met
    for j in stores:
        model.addConstr(
            gp.quicksum(x[i, j] for i in DCs) >= demand[j],
            name=f"demand_{j}"
        )

    # Capacity constraints: DC can only ship up to its capacity if opened
    for i in DCs:
        model.addConstr(
            gp.quicksum(x[i, j] for j in stores) <= capacity[i] * y[i],
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