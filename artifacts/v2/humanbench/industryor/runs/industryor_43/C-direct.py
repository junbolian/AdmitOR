import gurobipy as gp
from gurobipy import GRB

def solve(params):
    workers_initial = params["workers_initial"]
    prod_per_worker = params["prod_per_worker"]
    demand = params["demand"]  # list of 6 values
    overtime_max_per_worker = params["overtime_max_per_worker"]
    overtime_unit_cost = params["overtime_unit_cost"]
    holding_cost = params["holding_cost"]
    max_workforce_change = params["max_workforce_change"]
    hiring_cost = params["hiring_cost"]
    layoff_cost = params["layoff_cost"]
    initial_inventory = params["initial_inventory"]
    final_inventory = params["final_inventory"]

    T = len(demand)  # number of months (6)
    months = range(T)

    model = gp.Model("workforce_planning")
    model.setParam("OutputFlag", 0)

    # Decision variables
    # w[t]: number of workers in month t
    w = model.addVars(T, vtype=GRB.INTEGER, lb=0, name="w")
    # h[t]: workers hired at start of month t
    h = model.addVars(T, vtype=GRB.INTEGER, lb=0, name="h")
    # f[t]: workers laid off at start of month t
    f = model.addVars(T, vtype=GRB.INTEGER, lb=0, name="f")
    # o[t]: overtime units produced in month t
    o = model.addVars(T, vtype=GRB.INTEGER, lb=0, name="o")
    # inv[t]: inventory at end of month t
    inv = model.addVars(T, vtype=GRB.INTEGER, lb=0, name="inv")

    # Workforce evolution constraints
    for t in months:
        if t == 0:
            model.addConstr(w[t] == workers_initial + h[t] - f[t], name=f"workforce_{t}")
        else:
            model.addConstr(w[t] == w[t-1] + h[t] - f[t], name=f"workforce_{t}")

    # Max workforce change per month
    for t in months:
        model.addConstr(h[t] <= max_workforce_change, name=f"max_hire_{t}")
        model.addConstr(f[t] <= max_workforce_change, name=f"max_layoff_{t}")

    # Overtime capacity
    for t in months:
        model.addConstr(o[t] <= overtime_max_per_worker * w[t], name=f"overtime_cap_{t}")

    # Inventory balance
    for t in months:
        production = prod_per_worker * w[t] + o[t]
        if t == 0:
            model.addConstr(
                inv[t] == initial_inventory + production - demand[t],
                name=f"inv_balance_{t}"
            )
        else:
            model.addConstr(
                inv[t] == inv[t-1] + production - demand[t],
                name=f"inv_balance_{t}"
            )

    # Final inventory requirement
    model.addConstr(inv[T-1] == final_inventory, name="final_inventory")

    # Objective: minimize total cost
    total_cost = (
        gp.quicksum(overtime_unit_cost * o[t] for t in months)
        + gp.quicksum(holding_cost * inv[t] for t in months)
        + gp.quicksum(hiring_cost * h[t] + layoff_cost * f[t] for t in months)
    )
    model.setObjective(total_cost, GRB.MINIMIZE)

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}