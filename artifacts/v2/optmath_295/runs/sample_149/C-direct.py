import gurobipy as gp
from gurobipy import GRB

def solve(params):
    demand_A = params["demand_A_cumulative"]  # list of 5
    demand_B = params["demand_B_cumulative"]  # list of 5
    prod_cost_A = params["prod_cost_A"]
    prod_cost_B = params["prod_cost_B"]
    setup_cost_A = params["setup_cost_A"]
    setup_cost_B = params["setup_cost_B"]
    hold_cost_A = params["hold_cost_A"]
    hold_cost_B = params["hold_cost_B"]
    resource_use_A = params["resource_use_A"]
    resource_use_B = params["resource_use_B"]
    resource_capacity = params["resource_capacity"]
    max_prod_A = params["max_prod_A"]
    max_prod_B = params["max_prod_B"]

    T = 5
    periods = range(T)

    model = gp.Model("lot_sizing")
    model.setParam("OutputFlag", 0)

    # Production quantities
    x_A = model.addVars(T, lb=0.0, name="x_A")
    x_B = model.addVars(T, lb=0.0, name="x_B")

    # Setup binaries
    y_A = model.addVars(T, vtype=GRB.BINARY, name="y_A")
    y_B = model.addVars(T, vtype=GRB.BINARY, name="y_B")

    # Inventory levels (end of period t)
    inv_A = model.addVars(T, lb=0.0, name="inv_A")
    inv_B = model.addVars(T, lb=0.0, name="inv_B")

    # Inventory balance constraints
    # Cumulative production up to period t minus cumulative demand = inventory at end of t
    # inv_A[t] = sum(x_A[0..t]) - demand_A[t]
    # Equivalently: inv_A[t] = inv_A[t-1] + x_A[t] - (demand_A[t] - demand_A[t-1])
    for t in periods:
        if t == 0:
            period_demand_A = demand_A[0]
            period_demand_B = demand_B[0]
            model.addConstr(inv_A[t] == x_A[t] - period_demand_A, name=f"inv_bal_A_{t}")
            model.addConstr(inv_B[t] == x_B[t] - period_demand_B, name=f"inv_bal_B_{t}")
        else:
            period_demand_A = demand_A[t] - demand_A[t - 1]
            period_demand_B = demand_B[t] - demand_B[t - 1]
            model.addConstr(inv_A[t] == inv_A[t - 1] + x_A[t] - period_demand_A, name=f"inv_bal_A_{t}")
            model.addConstr(inv_B[t] == inv_B[t - 1] + x_B[t] - period_demand_B, name=f"inv_bal_B_{t}")

    # No inventory carried over at end of horizon
    model.addConstr(inv_A[T - 1] == 0, name="no_ending_inv_A")
    model.addConstr(inv_B[T - 1] == 0, name="no_ending_inv_B")

    # Production only if setup; production cannot exceed max limit
    for t in periods:
        model.addConstr(x_A[t] <= max_prod_A[t] * y_A[t], name=f"setup_A_{t}")
        model.addConstr(x_B[t] <= max_prod_B[t] * y_B[t], name=f"setup_B_{t}")

    # Resource capacity constraints
    for t in periods:
        model.addConstr(
            resource_use_A * x_A[t] + resource_use_B * x_B[t] <= resource_capacity[t],
            name=f"resource_{t}"
        )

    # Objective: production costs + setup costs + holding costs
    obj = gp.LinExpr()
    for t in periods:
        obj += prod_cost_A[t] * x_A[t]
        obj += prod_cost_B[t] * x_B[t]
        obj += setup_cost_A[t] * y_A[t]
        obj += setup_cost_B[t] * y_B[t]
        obj += hold_cost_A[t] * inv_A[t]
        obj += hold_cost_B[t] * inv_B[t]

    model.setObjective(obj, GRB.MINIMIZE)

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