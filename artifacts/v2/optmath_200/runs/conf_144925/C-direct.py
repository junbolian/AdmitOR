import gurobipy as gp
from gurobipy import GRB

def solve(params):
    fixed_setup_cost = params["fixed_setup_cost"]
    variable_production_cost = params["variable_production_cost"]
    inventory_holding_cost = params["inventory_holding_cost"]
    backlog_penalty = params["backlog_penalty"]
    production_capacity = params["production_capacity"]
    demand = params["demand"]

    T = 5  # number of periods

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Decision variables
    x = model.addVars(T, lb=0.0, name="x")          # production in period t
    y = model.addVars(T, vtype=GRB.BINARY, name="y") # setup decision in period t
    inv = model.addVars(T, lb=0.0, name="inv")       # inventory at end of period t
    b = model.addVars(T, lb=0.0, name="b")           # backlog at end of period t

    # Objective
    model.setObjective(
        gp.quicksum(
            fixed_setup_cost[t] * y[t]
            + variable_production_cost[t] * x[t]
            + inventory_holding_cost[t] * inv[t]
            + backlog_penalty[t] * b[t]
            for t in range(T)
        ),
        GRB.MINIMIZE
    )

    # Production capacity constraints
    for t in range(T):
        model.addConstr(x[t] <= production_capacity * y[t], name=f"cap_{t}")

    # Inventory balance constraints
    for t in range(T):
        inv_prev = 0.0 if t == 0 else inv[t - 1]
        b_prev = 0.0 if t == 0 else b[t - 1]
        model.addConstr(
            x[t] + inv_prev + b[t] == demand[t] + inv[t] + b_prev,
            name=f"balance_{t}"
        )

    # No inventory or backlog carried out of period 5
    model.addConstr(inv[T - 1] == 0, name="inv_end")
    model.addConstr(b[T - 1] == 0, name="b_end")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}