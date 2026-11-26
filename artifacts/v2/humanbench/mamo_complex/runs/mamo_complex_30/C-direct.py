import gurobipy as gp
from gurobipy import GRB

def solve(params):
    opening_costs = params["opening_costs"]
    transport_costs = params["transport_costs"]
    demands = params["demands"]
    capacities = params["capacities"]

    num_centers = 4
    num_stores = 6
    centers = range(num_centers)
    stores = range(num_stores)

    model = gp.Model("MarketFlow")
    model.setParam("OutputFlag", 0)

    # Decision variables
    # y[i] = 1 if center i is opened
    y = model.addVars(centers, vtype=GRB.BINARY, name="y")
    # x[i][j] = units shipped from center i to store j
    x = model.addVars(centers, stores, vtype=GRB.CONTINUOUS, lb=0.0, name="x")

    # Objective: minimize opening costs + transportation costs
    model.setObjective(
        gp.quicksum(opening_costs[i] * y[i] for i in centers) +
        gp.quicksum(transport_costs[i][j] * x[i, j] for i in centers for j in stores),
        GRB.MINIMIZE
    )

    # Demand constraints: each store's demand must be met
    for j in stores:
        model.addConstr(
            gp.quicksum(x[i, j] for i in centers) >= demands[j],
            name=f"demand_{j}"
        )

    # Capacity constraints: center can only ship if opened, up to its capacity
    for i in centers:
        model.addConstr(
            gp.quicksum(x[i, j] for j in stores) <= capacities[i] * y[i],
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