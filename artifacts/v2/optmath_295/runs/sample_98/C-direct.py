import gurobipy as gp
from gurobipy import GRB

def solve(params):
    demand = params["demand"]
    production_cost = params["production_cost"]
    setup_cost = params["setup_cost"]
    holding_cost = params["holding_cost"]
    capacity = params["capacity"]
    capacity_consumption = params["capacity_consumption"]

    num_products = 3
    num_months = 6
    products = range(num_products)
    months = range(num_months)

    # Precompute cumulative demand from month t onward for big-M in setup constraints
    # cum_demand_from[i][t] = sum of demand[i][t..T]
    cum_demand_from = []
    for i in products:
        row = []
        for t in months:
            row.append(sum(demand[i][s] for s in range(t, num_months)))
        cum_demand_from.append(row)

    model = gp.Model("lot_sizing")
    model.setParam("OutputFlag", 0)

    # Decision variables
    # x[i][t]: production quantity of product i in month t
    x = [[model.addVar(lb=0.0, name=f"x_{i}_{t}") for t in months] for i in products]

    # y[i][t]: binary setup variable
    y = [[model.addVar(vtype=GRB.BINARY, name=f"y_{i}_{t}") for t in months] for i in products]

    # inv[i][t]: inventory of product i at end of month t
    inv = [[model.addVar(lb=0.0, name=f"inv_{i}_{t}") for t in months] for i in products]

    # Objective: minimize total production + setup + holding costs
    obj = gp.LinExpr()
    for i in products:
        for t in months:
            obj += production_cost[i][t] * x[i][t]
            obj += setup_cost[i][t] * y[i][t]
            obj += holding_cost[i] * inv[i][t]
    model.setObjective(obj, GRB.MINIMIZE)

    # Inventory balance: inv[i][t] = inv[i][t-1] + x[i][t] - demand[i][t]
    # Equivalently: cumulative production - cumulative demand = inv[i][t] >= 0
    for i in products:
        for t in months:
            cum_prod = gp.quicksum(x[i][s] for s in range(t + 1))
            cum_dem = sum(demand[i][s] for s in range(t + 1))
            model.addConstr(cum_prod - cum_dem == inv[i][t], name=f"inv_balance_{i}_{t}")

    # Setup constraint: x[i][t] <= cum_demand_from[i][t] * y[i][t]
    for i in products:
        for t in months:
            big_m = cum_demand_from[i][t]
            model.addConstr(x[i][t] <= big_m * y[i][t], name=f"setup_{i}_{t}")

    # Capacity constraints: sum_i (capacity_consumption[i] * x[i][t]) <= capacity[t]
    for t in months:
        model.addConstr(
            gp.quicksum(capacity_consumption[i] * x[i][t] for i in products) <= capacity[t],
            name=f"capacity_{t}"
        )

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver_status_{status}"}