import gurobipy as gp
from gurobipy import GRB

def solve(params):
    demand_I = params["demand_I"]        # list of 12
    demand_II = params["demand_II"]      # list of 12
    cost_I = params["cost_I"]            # list of 12
    cost_II = params["cost_II"]          # list of 12
    production_capacity = params["production_capacity"]
    warehouse_capacity = params["warehouse_capacity"]
    space_I = params["space_I"]
    space_II = params["space_II"]
    own_storage_cost = params["own_storage_cost"]
    external_storage_cost = params["external_storage_cost"]

    months = range(12)  # 0..11

    model = gp.Model("production_planning")
    model.setParam("OutputFlag", 0)

    # Decision variables
    # prod_I[t], prod_II[t]: units produced in month t
    prod_I = model.addVars(months, lb=0.0, name="prod_I")
    prod_II = model.addVars(months, lb=0.0, name="prod_II")

    # inv_I[t], inv_II[t]: inventory at end of month t (units)
    inv_I = model.addVars(months, lb=0.0, name="inv_I")
    inv_II = model.addVars(months, lb=0.0, name="inv_II")

    # own_space[t]: cubic meters used in own warehouse at end of month t
    # ext_space[t]: cubic meters rented externally at end of month t
    own_space = model.addVars(months, lb=0.0, name="own_space")
    ext_space = model.addVars(months, lb=0.0, name="ext_space")

    # Inventory balance constraints (starting inventory = 0)
    for t in months:
        if t == 0:
            model.addConstr(inv_I[t] == prod_I[t] - demand_I[t], name=f"inv_bal_I_{t}")
            model.addConstr(inv_II[t] == prod_II[t] - demand_II[t], name=f"inv_bal_II_{t}")
        else:
            model.addConstr(inv_I[t] == inv_I[t-1] + prod_I[t] - demand_I[t], name=f"inv_bal_I_{t}")
            model.addConstr(inv_II[t] == inv_II[t-1] + prod_II[t] - demand_II[t], name=f"inv_bal_II_{t}")

    # Production capacity constraints
    for t in months:
        model.addConstr(prod_I[t] + prod_II[t] <= production_capacity, name=f"prod_cap_{t}")

    # Storage space linkage: total space = own + external
    for t in months:
        total_space_used = space_I * inv_I[t] + space_II * inv_II[t]
        model.addConstr(own_space[t] + ext_space[t] == total_space_used, name=f"storage_link_{t}")

    # Own warehouse capacity
    for t in months:
        model.addConstr(own_space[t] <= warehouse_capacity, name=f"own_cap_{t}")

    # Objective: production costs + own storage costs + external storage costs
    production_cost = gp.quicksum(
        cost_I[t] * prod_I[t] + cost_II[t] * prod_II[t]
        for t in months
    )
    storage_cost = gp.quicksum(
        own_storage_cost * own_space[t] + (own_storage_cost + external_storage_cost) * ext_space[t]
        for t in months
    )

    model.setObjective(production_cost + storage_cost, GRB.MINIMIZE)

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}


if __name__ == "__main__":
    params = {
        "demand_I": [10000, 10000, 10000, 10000,
                     30000, 30000, 30000, 30000, 30000,
                     100000, 100000, 100000],
        "demand_II": [50000, 50000,
                      15000, 15000, 15000, 15000, 15000, 15000, 15000,
                      50000, 50000, 50000],
        "cost_I": [5, 5, 5, 5, 5, 4.5, 4.5, 4.5, 4.5, 4.5, 4.5, 4.5],
        "cost_II": [8, 8, 8, 8, 8, 7, 7, 7, 7, 7, 7, 7],
        "production_capacity": 120000,
        "warehouse_capacity": 15000,
        "space_I": 0.2,
        "space_II": 0.4,
        "own_storage_cost": 1.0,
        "external_storage_cost": 1.5,
    }
    result = solve(params)
    print(result)