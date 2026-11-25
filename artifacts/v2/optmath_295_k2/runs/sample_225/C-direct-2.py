import gurobipy as gp
from gurobipy import GRB

def solve(params):
    cumulative_demand_A = params["cumulative_demand_A"]
    cumulative_demand_B = params["cumulative_demand_B"]
    production_cost_A = params["production_cost_A"]
    production_cost_B = params["production_cost_B"]
    setup_cost_A = params["setup_cost_A"]
    setup_cost_B = params["setup_cost_B"]
    holding_cost_A = params["holding_cost_A"]
    holding_cost_B = params["holding_cost_B"]
    resource_usage_A = params["resource_usage_A"]
    resource_usage_B = params["resource_usage_B"]
    resource_capacity = params["resource_capacity"]

    T = 6  # months 0..5

    # Derive period demands from cumulative demands
    # demand_t = cumulative_demand[t] - cumulative_demand[t-1], with cumulative_demand[-1] = 0
    demand_A = []
    demand_B = []
    for t in range(T):
        prev_A = cumulative_demand_A[t - 1] if t > 0 else 0
        prev_B = cumulative_demand_B[t - 1] if t > 0 else 0
        demand_A.append(cumulative_demand_A[t] - prev_A)
        demand_B.append(cumulative_demand_B[t] - prev_B)

    # Total remaining demand from month t onward (upper bound for production in month t)
    remaining_demand_A = []
    remaining_demand_B = []
    for t in range(T):
        remaining_demand_A.append(cumulative_demand_A[T - 1] - (cumulative_demand_A[t - 1] if t > 0 else 0))
        remaining_demand_B.append(cumulative_demand_B[T - 1] - (cumulative_demand_B[t - 1] if t > 0 else 0))

    model = gp.Model("production_planning")
    model.setParam("OutputFlag", 0)

    # Decision variables
    # x_A[t], x_B[t]: production quantities
    x_A = model.addVars(T, lb=0.0, name="x_A")
    x_B = model.addVars(T, lb=0.0, name="x_B")

    # y_A[t], y_B[t]: binary setup variables
    y_A = model.addVars(T, vtype=GRB.BINARY, name="y_A")
    y_B = model.addVars(T, vtype=GRB.BINARY, name="y_B")

    # inv_A[t], inv_B[t]: inventory at end of month t
    inv_A = model.addVars(T, lb=0.0, name="inv_A")
    inv_B = model.addVars(T, lb=0.0, name="inv_B")

    # Inventory balance constraints
    for t in range(T):
        prev_inv_A = inv_A[t - 1] if t > 0 else 0.0
        prev_inv_B = inv_B[t - 1] if t > 0 else 0.0
        model.addConstr(inv_A[t] == prev_inv_A + x_A[t] - demand_A[t], name=f"inv_bal_A_{t}")
        model.addConstr(inv_B[t] == prev_inv_B + x_B[t] - demand_B[t], name=f"inv_bal_B_{t}")

    # No inventory at end of planning horizon
    model.addConstr(inv_A[T - 1] == 0.0, name="end_inv_A")
    model.addConstr(inv_B[T - 1] == 0.0, name="end_inv_B")

    # Setup constraints: production only if setup is done; big-M = remaining demand
    for t in range(T):
        model.addConstr(x_A[t] <= remaining_demand_A[t] * y_A[t], name=f"setup_A_{t}")
        model.addConstr(x_B[t] <= remaining_demand_B[t] * y_B[t], name=f"setup_B_{t}")

    # Resource capacity constraints
    for t in range(T):
        model.addConstr(
            resource_usage_A * x_A[t] + resource_usage_B * x_B[t] <= resource_capacity[t],
            name=f"resource_{t}"
        )

    # Objective: minimize total production + setup + holding costs
    obj = gp.quicksum(
        production_cost_A[t] * x_A[t] + setup_cost_A[t] * y_A[t] + holding_cost_A[t] * inv_A[t]
        for t in range(T)
    ) + gp.quicksum(
        production_cost_B[t] * x_B[t] + setup_cost_B[t] * y_B[t] + holding_cost_B[t] * inv_B[t]
        for t in range(T)
    )
    model.setObjective(obj, GRB.MINIMIZE)

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}