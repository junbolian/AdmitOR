import gurobipy as gp
from gurobipy import GRB

def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]
    capacity = params["capacity"]

    num_warehouses = 5
    num_stores = 4

    model = gp.Model("transportation")
    model.setParam("OutputFlag", 0)

    x = model.addVars(num_warehouses, num_stores, lb=0.0, name="x")

    model.setObjective(
        gp.quicksum(cost[i][j] * x[i, j] for i in range(num_warehouses) for j in range(num_stores)),
        GRB.MINIMIZE
    )

    for i in range(num_warehouses):
        model.addConstr(
            gp.quicksum(x[i, j] for j in range(num_stores)) == supply[i],
            name=f"supply_{i}"
        )

    for j in range(num_stores):
        model.addConstr(
            gp.quicksum(x[i, j] for i in range(num_warehouses)) == demand[j],
            name=f"demand_{j}"
        )

    for i in range(num_warehouses):
        for j in range(num_stores):
            model.addConstr(x[i, j] <= capacity[i][j], name=f"cap_{i}_{j}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}