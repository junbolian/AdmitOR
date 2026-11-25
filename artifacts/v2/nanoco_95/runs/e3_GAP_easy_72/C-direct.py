import gurobipy as gp
from gurobipy import GRB

def solve(params):
    capacity = [
        params["capacity_DC1"],
        params["capacity_DC2"],
        params["capacity_DC3"],
    ]
    space = [
        params["space_DC1"],
        params["space_DC2"],
        params["space_DC3"],
    ]
    cost = [
        params["cost_DC1"],
        params["cost_DC2"],
        params["cost_DC3"],
    ]

    num_dcs = 3
    num_orders = 7
    dcs = range(num_dcs)
    orders = range(num_orders)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # x[d, o] = 1 if order o is assigned to DC d
    x = model.addVars(num_dcs, num_orders, vtype=GRB.BINARY, name="x")

    # Objective: minimize total shipping cost
    model.setObjective(
        gp.quicksum(cost[d][o] * x[d, o] for d in dcs for o in orders),
        GRB.MINIMIZE,
    )

    # Each order assigned to exactly one DC
    for o in orders:
        model.addConstr(gp.quicksum(x[d, o] for d in dcs) == 1, name=f"assign_{o}")

    # Capacity constraints
    for d in dcs:
        model.addConstr(
            gp.quicksum(space[d][o] * x[d, o] for o in orders) <= capacity[d],
            name=f"capacity_{d}",
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