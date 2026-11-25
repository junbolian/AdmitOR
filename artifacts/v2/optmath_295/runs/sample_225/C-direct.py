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

    T = 6  # months M0..M5
    months = range(T)

    # Derive per-period demands from cumulative
    demand_A = []
    demand_B = []
    for t in months:
        if t == 0:
            demand_A.append(cumulative_demand_A[0])
            demand_B.append(cumulative_demand_B[0])
        else:
            demand_A.append(cumulative_demand_A[t] - cumulative_demand_A[t - 1])
            demand_B.append(cumulative_demand_B[t] - cumulative_demand_B[t - 1])

    # Total remaining demand from month t onward (upper bound for production)
    remaining_A = []
    remaining_B = []
    total_A = cumulative_demand_A[T - 1]
    total_B = cumulative_demand_B[T - 1]
    for t in months:
        remaining_A.append(total_A - (cumulative_demand_A[t - 1] if t > 0 else 0))
        remaining_B.append(total_B - (cumulative_demand_B[t - 1] if t > 0 else 0))

    model = gp.Model("lot_sizing")
    model.setParam("OutputFlag", 0)

    # Decision variables
    prod_A = model.addVars(T, lb=0.0, name="prod_A")
    prod_B = model.addVars(T, lb=0.0, name="prod_B")
    inv_A = model.addVars(T, lb=0.0, name="inv_A")
    inv_B = model.addVars(T, lb=0.0, name="inv_B")
    setup_A = model.addVars(T, vtype=GRB.BINARY, name="setup_A")
    setup_B = model.addVars(T, vtype=GRB.BINARY, name="setup_B")

    # Objective: minimize total production + setup + holding costs
    obj = gp.quicksum(
        production_cost_A[t] * prod_A[t] +
        setup_cost_A[t] * setup_A[t] +
        holding_cost_A[t] * inv_A[t]
        for t in months
    ) + gp.quicksum(
        production_cost_B[t] * prod_B[t] +
        setup_cost_B[t] * setup_B[t] +
        holding_cost_B[t] * inv_B[t]
        for t in months
    )
    model.setObjective(obj, GRB.MINIMIZE)

    # Inventory balance constraints
    for t in months:
        prev_inv_A = 0.0 if t == 0 else inv_A[t - 1]
        prev_inv_B = 0.0 if t == 0 else inv_B[t - 1]
        model.addConstr(
            inv_A[t] == prev_inv_A + prod_A[t] - demand_A[t],
            name=f"inv_balance_A_{t}"
        )
        model.addConstr(
            inv_B[t] == prev_inv_B + prod_B[t] - demand_B[t],
            name=f"inv_balance_B_{t}"
        )

    # No inventory carried at the end of the horizon
    model.addConstr(inv_A[T - 1] == 0.0, name="no_end_inv_A")
    model.addConstr(inv_B[T - 1] == 0.0, name="no_end_inv_B")

    # Setup linking: production only if setup is active; bound by remaining demand
    for t in months:
        model.addConstr(prod_A[t] <= remaining_A[t] * setup_A[t], name=f"setup_link_A_{t}")
        model.addConstr(prod_B[t] <= remaining_B[t] * setup_B[t], name=f"setup_link_B_{t}")

    # Resource capacity constraints
    for t in months:
        model.addConstr(
            resource_usage_A * prod_A[t] + resource_usage_B * prod_B[t] <= resource_capacity[t],
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
        return {"objective": None, "status": f"solver_status_{status}"}