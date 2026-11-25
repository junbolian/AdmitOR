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
    capacity = params["capacity"]
    resource_use_A = params["resource_use_A"]
    resource_use_B = params["resource_use_B"]
    max_prod_A = params["max_prod_A"]
    max_prod_B = params["max_prod_B"]

    T = 7
    weeks = range(T)

    model = gp.Model("production_planning")
    model.setParam("OutputFlag", 0)

    # Decision variables
    prod_A = [model.addVar(lb=0.0, name=f"prod_A_{t}") for t in weeks]
    prod_B = [model.addVar(lb=0.0, name=f"prod_B_{t}") for t in weeks]
    inv_A = [model.addVar(lb=0.0, name=f"inv_A_{t}") for t in weeks]
    inv_B = [model.addVar(lb=0.0, name=f"inv_B_{t}") for t in weeks]
    setup_A = [model.addVar(vtype=GRB.BINARY, name=f"setup_A_{t}") for t in weeks]
    setup_B = [model.addVar(vtype=GRB.BINARY, name=f"setup_B_{t}") for t in weeks]

    # Objective: minimize total production + setup + holding costs
    obj = gp.quicksum(
        prod_cost_A[t] * prod_A[t] + setup_cost_A[t] * setup_A[t] + hold_cost_A[t] * inv_A[t] +
        prod_cost_B[t] * prod_B[t] + setup_cost_B[t] * setup_B[t] + hold_cost_B[t] * inv_B[t]
        for t in weeks
    )
    model.setObjective(obj, GRB.MINIMIZE)

    # Inventory balance constraints
    for t in weeks:
        if t == 0:
            # Initial inventory is 0
            model.addConstr(prod_A[t] - demand_A[t] == inv_A[t], name=f"inv_bal_A_{t}")
            model.addConstr(prod_B[t] - demand_B[t] == inv_B[t], name=f"inv_bal_B_{t}")
        else:
            model.addConstr(inv_A[t-1] + prod_A[t] - demand_A[t] == inv_A[t], name=f"inv_bal_A_{t}")
            model.addConstr(inv_B[t-1] + prod_B[t] - demand_B[t] == inv_B[t], name=f"inv_bal_B_{t}")

    # Resource capacity constraints
    for t in weeks:
        model.addConstr(
            resource_use_A * prod_A[t] + resource_use_B * prod_B[t] <= capacity[t],
            name=f"capacity_{t}"
        )

    # Setup constraints: production only if setup binary is 1
    for t in weeks:
        model.addConstr(prod_A[t] <= max_prod_A[t] * setup_A[t], name=f"setup_link_A_{t}")
        model.addConstr(prod_B[t] <= max_prod_B[t] * setup_B[t], name=f"setup_link_B_{t}")

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