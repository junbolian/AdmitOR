import gurobipy as gp
from gurobipy import GRB

def solve(params):
    initial_stock = params["initial_stock"]
    required_demand = params["required_demand"]
    transport_cost = params["transport_cost"]

    n = len(initial_stock)
    warehouses = range(n)

    model = gp.Model("food_distribution")
    model.setParam("OutputFlag", 0)

    # x[i][j] = tons moved from warehouse i to warehouse j
    x = [[None] * n for _ in warehouses]
    for i in warehouses:
        for j in warehouses:
            if i != j:
                x[i][j] = model.addVar(lb=0.0, name=f"x_{i}_{j}")

    # Objective: minimize total transportation cost
    obj = gp.LinExpr()
    for i in warehouses:
        for j in warehouses:
            if i != j:
                obj += transport_cost[i][j] * x[i][j]
    model.setObjective(obj, GRB.MINIMIZE)

    # Each warehouse's final stock = initial + inflow - outflow >= required_demand
    for i in warehouses:
        inflow = gp.LinExpr()
        outflow = gp.LinExpr()
        for j in warehouses:
            if i != j:
                inflow += x[j][i]
                outflow += x[i][j]
        model.addConstr(
            initial_stock[i] + inflow - outflow >= required_demand[i],
            name=f"demand_{i}"
        )

    # Cannot ship more than current stock out of a warehouse
    for i in warehouses:
        outflow = gp.LinExpr()
        for j in warehouses:
            if i != j:
                outflow += x[i][j]
        model.addConstr(outflow <= initial_stock[i], name=f"supply_{i}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}