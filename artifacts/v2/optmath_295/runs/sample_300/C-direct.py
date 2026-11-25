import gurobipy as gp
from gurobipy import GRB

def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    transport_cost = params["transport_cost"]
    shipping_capacity = params["shipping_capacity"]

    n_warehouses = 5
    n_stores = 6
    n_products = 2

    model = gp.Model("distribution")
    model.Params.OutputFlag = 0

    x = model.addVars(n_warehouses, n_stores, n_products, lb=0, name="ship")

    model.setObjective(
        gp.quicksum(
            transport_cost[i][j][p] * x[i, j, p]
            for i in range(n_warehouses)
            for j in range(n_stores)
            for p in range(n_products)
        ),
        GRB.MINIMIZE,
    )

    for i in range(n_warehouses):
        for p in range(n_products):
            model.addConstr(
                gp.quicksum(x[i, j, p] for j in range(n_stores)) <= supply[i][p]
            )

    for j in range(n_stores):
        for p in range(n_products):
            model.addConstr(
                gp.quicksum(x[i, j, p] for i in range(n_warehouses)) >= demand[j][p]
            )

    for i in range(n_warehouses):
        for j in range(n_stores):
            model.addConstr(
                gp.quicksum(x[i, j, p] for p in range(n_products)) <= shipping_capacity[i][j]
            )

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.objVal), "status": "optimal"}
    elif model.status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"failed_status_{model.status}"}