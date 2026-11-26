import gurobipy as gp
from gurobipy import GRB

def solve(params):
    demand_A1 = params["demand_A1"]           # list of 4
    demand_A2 = params["demand_A2"]           # list of 4
    demand_A3 = params["demand_A3"]           # list of 4
    price = params["price"]                   # list of 3
    production_cost = params["production_cost"]  # list of 3
    activation_cost = params["activation_cost"]  # list of 3
    production_quota = params["production_quota"]  # list of 3
    min_batch_size = params["min_batch_size"]     # list of 3
    production_days = params["production_days"]   # list of 4
    storage_cost = params["storage_cost"]         # list of 3
    storage_capacity = params["storage_capacity"] # scalar

    num_products = 3
    num_months = 4
    products = range(num_products)
    months = range(num_months)

    demand = [demand_A1, demand_A2, demand_A3]

    model = gp.Model("production_planning")
    model.setParam("OutputFlag", 0)

    # x[i][t]: units produced of product i in month t
    x = [[model.addVar(lb=0.0, name=f"x_{i}_{t}") for t in months] for i in products]

    # s[i][t]: units stored of product i at end of month t
    s = [[model.addVar(lb=0.0, name=f"s_{i}_{t}") for t in months] for i in products]

    # q[i][t]: units sold of product i in month t (sales <= demand)
    q = [[model.addVar(lb=0.0, name=f"q_{i}_{t}") for t in months] for i in products]

    # y[i][t]: binary, 1 if production line i is active in month t
    y = [[model.addVar(vtype=GRB.BINARY, name=f"y_{i}_{t}") for t in months] for i in products]

    # Inventory balance: prev_stock + x[i][t] - s[i][t] = q[i][t]
    # (produced + carried in = sold + carried out)
    for i in products:
        for t in months:
            prev_stock = s[i][t - 1] if t > 0 else 0.0
            model.addConstr(
                prev_stock + x[i][t] - s[i][t] == q[i][t],
                name=f"balance_{i}_{t}"
            )

    # Sales cannot exceed demand
    for i in products:
        for t in months:
            model.addConstr(
                q[i][t] <= demand[i][t],
                name=f"demand_{i}_{t}"
            )

    # Production quota: x[i][t] <= production_quota[i] * production_days[t] * y[i][t]
    for i in products:
        for t in months:
            model.addConstr(
                x[i][t] <= production_quota[i] * production_days[t] * y[i][t],
                name=f"quota_{i}_{t}"
            )

    # Minimum batch size: x[i][t] >= min_batch_size[i] * y[i][t]
    for i in products:
        for t in months:
            model.addConstr(
                x[i][t] >= min_batch_size[i] * y[i][t],
                name=f"min_batch_{i}_{t}"
            )

    # Storage capacity: sum over products of s[i][t] <= storage_capacity for each month
    for t in months:
        model.addConstr(
            gp.quicksum(s[i][t] for i in products) <= storage_capacity,
            name=f"storage_cap_{t}"
        )

    # Objective: maximize profit = revenue - production costs - activation costs - storage costs
    revenue = gp.quicksum(
        price[i] * q[i][t]
        for i in products for t in months
    )

    prod_costs = gp.quicksum(
        production_cost[i] * x[i][t]
        for i in products for t in months
    )

    act_costs = gp.quicksum(
        activation_cost[i] * y[i][t]
        for i in products for t in months
    )

    stor_costs = gp.quicksum(
        storage_cost[i] * s[i][t]
        for i in products for t in months
    )

    model.setObjective(revenue - prod_costs - act_costs - stor_costs, GRB.MAXIMIZE)

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}