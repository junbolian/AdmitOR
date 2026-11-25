import gurobipy as gp
from gurobipy import GRB

def solve(params):
    fixed_cost = params["fixed_cost"]
    shipping_cost = params["shipping_cost"]
    demand = params["demand"]
    capacity = params["capacity"]

    num_dc = 7
    num_stores = 8

    model = gp.Model("facility_location")
    model.Params.OutputFlag = 0

    y = model.addVars(num_dc, vtype=GRB.BINARY, name="y")
    x = model.addVars(num_dc, num_stores, vtype=GRB.CONTINUOUS, lb=0, name="x")

    model.setObjective(
        gp.quicksum(fixed_cost[i] * y[i] for i in range(num_dc))
        + gp.quicksum(
            shipping_cost[i][j] * x[i, j]
            for i in range(num_dc)
            for j in range(num_stores)
        ),
        GRB.MINIMIZE,
    )

    for j in range(num_stores):
        model.addConstr(
            gp.quicksum(x[i, j] for i in range(num_dc)) == demand[j],
            name=f"demand_{j}",
        )

    for i in range(num_dc):
        model.addConstr(
            gp.quicksum(x[i, j] for j in range(num_stores)) <= capacity[i] * y[i],
            name=f"capacity_{i}",
        )

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"status_{model.status}"}