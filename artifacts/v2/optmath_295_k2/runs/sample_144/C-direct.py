import gurobipy as gp
from gurobipy import GRB

def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    transport_cost = params["transport_cost"]

    num_warehouses = 12
    num_stores = 14

    warehouses = range(num_warehouses)
    stores = range(num_stores)

    model = gp.Model("transportation")
    model.setParam("OutputFlag", 0)

    x = model.addVars(warehouses, stores, lb=0.0, name="x")

    model.setObjective(
        gp.quicksum(transport_cost[i][j] * x[i, j] for i in warehouses for j in stores),
        GRB.MINIMIZE
    )

    for i in warehouses:
        model.addConstr(
            gp.quicksum(x[i, j] for j in stores) == supply[i],
            name=f"supply_{i}"
        )

    for j in stores:
        model.addConstr(
            gp.quicksum(x[i, j] for i in warehouses) == demand[j],
            name=f"demand_{j}"
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