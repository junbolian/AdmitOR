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
    # demand_A[t] = cumulative_demand_A[t] - cumulative_demand_A[t-1], demand_A[0] = cumulative_demand_A[0]
    demand_A = [cumulative_demand_A[0]] + [cumulative_demand_A[t] - cumulative_demand_A[t-1] for t in range(1, T)]
    demand_B = [cumulative_demand_B[0]] + [cumulative_demand_B[t] - cumulative_demand_B[t-1] for t in range(1, T)]

    # Total remaining demand from month t onward (upper bound for production in month t)
    # production in month t cannot exceed cumulative demand from t onward
    remaining_A = [cumulative_demand_A[T-1] - (cumulative_demand_A[t-1] if t > 0 else 0) for t in range(T)]
    remaining_B = [cumulative_demand_B[T-1] - (cumulative_demand_B[t-1] if t > 0 else 0) for t in range(T)]

    model = gp.Model("lot_sizing")
    model.setParam("OutputFlag", 0)

    # Decision variables
    # x_A[t], x_B[t]: production quantities
    # y_A[t], y_B[t]: binary setup variables
    # inv_A[t], inv_B[t]: end-of-month inventory

    x_A = model.addVars(T, lb=0.0, name="x_A")
    x_B = model.addVars(T, lb=0.0, name="x_B")
    y_A = model.addVars(T, vtype=GRB.BINARY, name="y_A")
    y_B = model.addVars(T, vtype=GRB.BINARY, name="y_B")
    inv_A = model.addVars(T, lb=0.0, name="inv_A")
    inv_B = model.addVars(T, lb=0.0, name="inv_B")

    # Objective: minimize production + setup + holding costs
    obj = gp.quicksum(
        production_cost_A[t] * x_A[t] + setup_cost_A[t] * y_A[t] + holding_cost_A[t] * inv_A[t]
        for t in range(T)
    ) + gp.quicksum(
        production_cost_B[t] * x_B[t] + setup_cost_B[t] * y_B[t] + holding_cost_B[t] * inv_B[t]
        for t in range(T)
    )
    model.setObjective(obj, GRB.MINIMIZE)

    # Inventory balance constraints
    # No initial inventory (inv at start = 0)
    for t in range(T):
        prev_inv_A = inv_A[t-1] if t > 0 else 0.0
        prev_inv_B = inv_B[t-1] if t > 0 else 0.0
        model.addConstr(inv_A[t] == prev_inv_A + x_A[t] - demand_A[t], name=f"inv_bal_A_{t}")
        model.addConstr(inv_B[t] == prev_inv_B + x_B[t] - demand_B[t], name=f"inv_bal_B_{t}")

    # No inventory at end of planning horizon
    model.addConstr(inv_A[T-1] == 0.0, name="no_end_inv_A")
    model.addConstr(inv_B[T-1] == 0.0, name="no_end_inv_B")

    # Setup constraints: production only if setup occurred; production bounded by remaining demand
    for t in range(T):
        model.addConstr(x_A[t] <= remaining_A[t] * y_A[t], name=f"setup_A_{t}")
        model.addConstr(x_B[t] <= remaining_B[t] * y_B[t], name=f"setup_B_{t}")

    # Resource capacity constraints
    for t in range(T):
        model.addConstr(
            resource_usage_A * x_A[t] + resource_usage_B * x_B[t] <= resource_capacity[t],
            name=f"resource_{t}"
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
        return {"objective": None, "status": f"gurobi_status_{status}"}