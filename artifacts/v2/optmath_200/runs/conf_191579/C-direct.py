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
    usage_A = params["usage_A"]
    usage_B = params["usage_B"]
    prod_ub_A = params["prod_ub_A"]
    prod_ub_B = params["prod_ub_B"]

    T = 4
    periods = range(T)

    # Normalize all params to lists of length T
    def to_list(val, length):
        if isinstance(val, (int, float)):
            return [val] * length
        return list(val)

    demand_A = to_list(demand_A, T)
    demand_B = to_list(demand_B, T)
    prod_cost_A = to_list(prod_cost_A, T)
    prod_cost_B = to_list(prod_cost_B, T)
    setup_cost_A = to_list(setup_cost_A, T)
    setup_cost_B = to_list(setup_cost_B, T)
    hold_cost_A = to_list(hold_cost_A, T)
    hold_cost_B = to_list(hold_cost_B, T)
    capacity = to_list(capacity, T)
    usage_A = to_list(usage_A, T)
    usage_B = to_list(usage_B, T)
    prod_ub_A = to_list(prod_ub_A, T)
    prod_ub_B = to_list(prod_ub_B, T)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    x_A = model.addVars(T, lb=0.0, name="x_A")
    x_B = model.addVars(T, lb=0.0, name="x_B")
    y_A = model.addVars(T, vtype=GRB.BINARY, name="y_A")
    y_B = model.addVars(T, vtype=GRB.BINARY, name="y_B")
    inv_A = model.addVars(T, lb=0.0, name="inv_A")
    inv_B = model.addVars(T, lb=0.0, name="inv_B")

    obj = gp.quicksum(
        prod_cost_A[t] * x_A[t] + setup_cost_A[t] * y_A[t] + hold_cost_A[t] * inv_A[t]
        + prod_cost_B[t] * x_B[t] + setup_cost_B[t] * y_B[t] + hold_cost_B[t] * inv_B[t]
        for t in periods
    )
    model.setObjective(obj, GRB.MINIMIZE)

    for t in periods:
        if t == 0:
            model.addConstr(inv_A[t] == x_A[t] - demand_A[t], name=f"bal_A_{t}")
            model.addConstr(inv_B[t] == x_B[t] - demand_B[t], name=f"bal_B_{t}")
        else:
            model.addConstr(inv_A[t] == inv_A[t-1] + x_A[t] - demand_A[t], name=f"bal_A_{t}")
            model.addConstr(inv_B[t] == inv_B[t-1] + x_B[t] - demand_B[t], name=f"bal_B_{t}")

    for t in periods:
        model.addConstr(
            usage_A[t] * x_A[t] + usage_B[t] * x_B[t] <= capacity[t],
            name=f"cap_{t}"
        )

    for t in periods:
        model.addConstr(x_A[t] <= prod_ub_A[t] * y_A[t], name=f"ub_A_{t}")
        model.addConstr(x_B[t] <= prod_ub_B[t] * y_B[t], name=f"ub_B_{t}")

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