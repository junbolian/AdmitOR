import gurobipy as gp
from gurobipy import GRB

def solve(params):
    capacity = [
        params["capacity_DC1"],
        params["capacity_DC2"],
        params["capacity_DC3"],
    ]
    storage = [
        params["storage_DC1"],
        params["storage_DC2"],
        params["storage_DC3"],
    ]
    cost = [
        params["cost_DC1"],
        params["cost_DC2"],
        params["cost_DC3"],
    ]

    n_dc = 3
    n_orders = 7
    dcs = range(n_dc)
    orders = range(n_orders)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # x[i][j] = 1 if order j is assigned to DC i
    x = [[model.addVar(vtype=GRB.BINARY, name=f"x_{i}_{j}") for j in orders] for i in dcs]

    # Objective: minimize total shipping cost
    model.setObjective(
        gp.quicksum(cost[i][j] * x[i][j] for i in dcs for j in orders),
        GRB.MINIMIZE,
    )

    # Each order assigned to exactly one DC
    for j in orders:
        model.addConstr(gp.quicksum(x[i][j] for i in dcs) == 1, name=f"assign_{j}")

    # Capacity constraints
    for i in dcs:
        model.addConstr(
            gp.quicksum(storage[i][j] * x[i][j] for j in orders) <= capacity[i],
            name=f"capacity_{i}",
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