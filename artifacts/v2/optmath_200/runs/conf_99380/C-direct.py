import gurobipy as gp
from gurobipy import GRB

def solve(params):
    demand_A = params["demand_A"]
    demand_B = params["demand_B"]
    prod_cost_A = params["prod_cost_A"]
    prod_cost_B = params["prod_cost_B"]
    setup_cost_A = params["setup_cost_A"]
    setup_cost_B = params["setup_cost_B"]
    hold_cost_A = params["hold_cost_A"]
    hold_cost_B = params["hold_cost_B"]
    resource_usage_A = params["resource_usage_A"]
    resource_usage_B = params["resource_usage_B"]
    resource_capacity = params["resource_capacity"]

    T = 7  # periods 0..6
    periods = range(T)

    # Compute per-period demands from cumulative demands
    # period_demand[t] = cumulative[t] - cumulative[t-1], with cumulative[-1] = 0
    per_demand_A = [demand_A[0]] + [demand_A[t] - demand_A[t-1] for t in range(1, T)]
    per_demand_B = [demand_B[0]] + [demand_B[t] - demand_B[t-1] for t in range(1, T)]

    model = gp.Model("lot_sizing")
    model.setParam("OutputFlag", 0)

    # Decision variables
    # x_A[t]: production quantity of Product A in period t
    # x_B[t]: production quantity of Product B in period t
    # inv_A[t]: inventory of Product A at end of period t
    # inv_B[t]: inventory of Product B at end of period t
    # y_A[t]: binary setup variable for Product A in period t
    # y_B[t]: binary setup variable for Product B in period t

    x_A = model.addVars(T, lb=0.0, name="x_A")
    x_B = model.addVars(T, lb=0.0, name="x_B")
    inv_A = model.addVars(T, lb=0.0, name="inv_A")
    inv_B = model.addVars(T, lb=0.0, name="inv_B")
    y_A = model.addVars(T, vtype=GRB.BINARY, name="y_A")
    y_B = model.addVars(T, vtype=GRB.BINARY, name="y_B")

    # Objective: minimize total production + setup + holding costs
    obj = gp.quicksum(
        prod_cost_A[t] * x_A[t] + setup_cost_A[t] * y_A[t] + hold_cost_A[t] * inv_A[t] +
        prod_cost_B[t] * x_B[t] + setup_cost_B[t] * y_B[t] + hold_cost_B[t] * inv_B[t]
        for t in periods
    )
    model.setObjective(obj, GRB.MINIMIZE)

    # Inventory balance constraints
    # inv_A[t] = inv_A[t-1] + x_A[t] - per_demand_A[t], with inv_A[-1] = 0
    for t in periods:
        prev_inv_A = inv_A[t-1] if t > 0 else 0.0
        prev_inv_B = inv_B[t-1] if t > 0 else 0.0
        model.addConstr(inv_A[t] == prev_inv_A + x_A[t] - per_demand_A[t], name=f"bal_A_{t}")
        model.addConstr(inv_B[t] == prev_inv_B + x_B[t] - per_demand_B[t], name=f"bal_B_{t}")

    # Resource capacity constraints
    for t in periods:
        model.addConstr(
            resource_usage_A * x_A[t] + resource_usage_B * x_B[t] <= resource_capacity[t],
            name=f"resource_{t}"
        )

    # Setup constraints: production only if setup is active
    # Big-M: use total remaining demand as upper bound
    total_demand_A = demand_A[T-1]
    total_demand_B = demand_B[T-1]

    for t in periods:
        model.addConstr(x_A[t] <= total_demand_A * y_A[t], name=f"setup_A_{t}")
        model.addConstr(x_B[t] <= total_demand_B * y_B[t], name=f"setup_B_{t}")

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