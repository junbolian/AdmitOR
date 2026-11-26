import gurobipy as gp
from gurobipy import GRB

def solve(params):
    demand = params["demand"]           # list of 4 values
    capacity = params["capacity"]       # list of 4 values
    production_cost = params["production_cost"]  # list of 4 values
    storage_cost = params["storage_cost"]        # scalar

    n_weeks = 4
    weeks = range(n_weeks)

    model = gp.Model("beverage_production")
    model.setParam("OutputFlag", 0)

    # Decision variables
    # x[t]: production quantity in week t (thousand boxes)
    x = model.addVars(n_weeks, lb=0.0, name="x")

    # s[t]: inventory carried over at end of week t (thousand boxes)
    # s[t] >= 0, with s[-1] = 0 (no initial inventory)
    s = model.addVars(n_weeks, lb=0.0, name="s")

    # Capacity constraints
    for t in weeks:
        model.addConstr(x[t] <= capacity[t], name=f"cap_{t}")

    # Inventory balance constraints
    # s[t] = s[t-1] + x[t] - demand[t], with s[-1] = 0
    for t in weeks:
        if t == 0:
            model.addConstr(s[t] == x[t] - demand[t], name=f"inv_bal_{t}")
        else:
            model.addConstr(s[t] == s[t - 1] + x[t] - demand[t], name=f"inv_bal_{t}")

    # No leftover inventory after week 4 (optional: can relax if not stated)
    # The problem says "meet weekly demand" but doesn't require zero ending stock.
    # We allow s[3] >= 0 naturally; minimizing cost will drive it to zero anyway.

    # Objective: minimize total production cost + total storage cost
    total_prod_cost = gp.quicksum(production_cost[t] * x[t] for t in weeks)
    total_stor_cost = gp.quicksum(storage_cost * s[t] for t in weeks)
    model.setObjective(total_prod_cost + total_stor_cost, GRB.MINIMIZE)

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