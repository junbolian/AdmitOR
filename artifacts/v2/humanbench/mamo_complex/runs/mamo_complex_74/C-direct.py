import gurobipy as gp
from gurobipy import GRB

def solve(params):
    demand = params["demand"]                          # list of 6 monthly demands
    regular_capacity = params["regular_capacity"]      # scalar or list
    regular_cost = params["regular_cost"]              # cost per wrench (regular)
    overtime_capacity = params["overtime_capacity"]    # scalar or list
    overtime_cost = params["overtime_cost"]            # cost per wrench (overtime)
    holding_cost = params["holding_cost"]              # cost per wrench per month
    initial_inventory = params["initial_inventory"]    # inventory at start of Jan

    T = 6  # number of months (Jan–Jun)
    months = range(T)

    # Normalize capacities to lists if scalar
    if not hasattr(regular_capacity, '__len__'):
        reg_cap = [regular_capacity] * T
    else:
        reg_cap = list(regular_capacity)

    if not hasattr(overtime_capacity, '__len__'):
        ot_cap = [overtime_capacity] * T
    else:
        ot_cap = list(overtime_capacity)

    demand_list = list(demand)

    model = gp.Model("BTD_production")
    model.setParam("OutputFlag", 0)

    # Decision variables
    # r[t]: regular-time production in month t
    r = model.addVars(T, lb=0.0, name="r")
    # o[t]: overtime production in month t
    o = model.addVars(T, lb=0.0, name="o")
    # inv[t]: inventory at END of month t (after satisfying demand)
    inv = model.addVars(T, lb=0.0, name="inv")

    # Capacity constraints
    for t in months:
        model.addConstr(r[t] <= reg_cap[t], name=f"reg_cap_{t}")
        model.addConstr(o[t] <= ot_cap[t], name=f"ot_cap_{t}")

    # Inventory balance constraints
    # inv[t] = inv[t-1] + r[t] + o[t] - demand[t]
    for t in months:
        prev_inv = initial_inventory if t == 0 else inv[t - 1]
        model.addConstr(
            inv[t] == prev_inv + r[t] + o[t] - demand_list[t],
            name=f"inv_balance_{t}"
        )

    # Objective: minimize total cost
    total_cost = (
        gp.quicksum(regular_cost * r[t] + overtime_cost * o[t] for t in months)
        + gp.quicksum(holding_cost * inv[t] for t in months)
    )
    model.setObjective(total_cost, GRB.MINIMIZE)

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": round(model.ObjVal), "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}