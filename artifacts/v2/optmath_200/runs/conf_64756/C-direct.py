import gurobipy as gp
from gurobipy import GRB

def solve(params):
    production_cost = params["production_cost"]
    setup_cost = params["setup_cost"]
    holding_cost = params["holding_cost"]
    cumulative_demand = params["cumulative_demand"]
    resource_capacity = params["resource_capacity"]
    resource_consumption = params["resource_consumption"]
    max_production_if_setup = params["max_production_if_setup"]

    n_products = 3
    n_periods = 5
    products = range(n_products)
    periods = range(n_periods)

    model = gp.Model("lot_sizing")
    model.setParam("OutputFlag", 0)

    # Decision variables
    # Production quantity for product i in period t
    x = model.addVars(n_products, n_periods, lb=0.0, name="x")
    # Binary setup variable
    y = model.addVars(n_products, n_periods, vtype=GRB.BINARY, name="y")
    # Inventory at end of period t (index 0..4 represents end of periods 0..4)
    inv = model.addVars(n_products, n_periods, lb=0.0, name="inv")

    # Objective: minimize total production + setup + holding costs
    obj = gp.quicksum(
        production_cost[i][t] * x[i, t] +
        setup_cost[i][t] * y[i, t] +
        holding_cost[i][t] * inv[i, t]
        for i in products for t in periods
    )
    model.setObjective(obj, GRB.MINIMIZE)

    # Inventory balance constraints
    # Cumulative production up to period t minus cumulative demand up to period t = inventory at end of period t
    # inv[i,t] = sum_{s=0}^{t} x[i,s] - cumulative_demand[i][t]
    # Equivalently: inv[i,t] - inv[i,t-1] = x[i,t] - (cumulative_demand[i][t] - cumulative_demand[i][t-1])
    # Initial inventory = 0, final inventory = 0

    for i in products:
        for t in periods:
            if t == 0:
                # inv[i,0] = x[i,0] - cumulative_demand[i][0]
                model.addConstr(inv[i, t] == x[i, t] - cumulative_demand[i][t], name=f"inv_bal_{i}_{t}")
            else:
                # inv[i,t] = inv[i,t-1] + x[i,t] - (cumulative_demand[i][t] - cumulative_demand[i][t-1])
                period_demand = cumulative_demand[i][t] - cumulative_demand[i][t - 1]
                model.addConstr(inv[i, t] == inv[i, t - 1] + x[i, t] - period_demand, name=f"inv_bal_{i}_{t}")

    # Final inventory must be zero
    for i in products:
        model.addConstr(inv[i, n_periods - 1] == 0.0, name=f"final_inv_{i}")

    # Production only if setup
    for i in products:
        for t in periods:
            model.addConstr(x[i, t] <= max_production_if_setup[i][t] * y[i, t], name=f"setup_{i}_{t}")

    # Resource capacity constraints
    for t in periods:
        model.addConstr(
            gp.quicksum(resource_consumption[i] * x[i, t] for i in products) <= resource_capacity[t],
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
        return {"objective": None, "status": f"status_{status}"}