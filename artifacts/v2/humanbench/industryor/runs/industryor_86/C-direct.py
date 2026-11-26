import gurobipy as gp
from gurobipy import GRB

def solve(params):
    demand = params["demand"]       # list of 4 demands, indexed 0..3
    cost_1 = params["cost_1"]
    cost_2 = params["cost_2"]
    cost_3 = params["cost_3"]
    cost_4 = params["cost_4"]

    # x[i][d] = area (m^2) rented at the start of month i+1 for d+1 months
    # i in 0..3 (start month), d in 0..3 (duration 1..4), valid when i+d <= 3
    # cost[d] = cost per m^2 for a contract of length d+1 months
    costs = [cost_1, cost_2, cost_3, cost_4]

    model = gp.Model("warehouse_rental")
    model.setParam("OutputFlag", 0)

    # Decision variables: x[i][d] >= 0
    # i = start month index (0-based), d = duration index (0-based, duration = d+1)
    x = {}
    for i in range(4):
        for d in range(4):
            if i + d <= 3:   # contract starting at month i+1 lasting d+1 months ends at month i+d+1
                x[i, d] = model.addVar(lb=0.0, vtype=GRB.CONTINUOUS, name=f"x_{i}_{d}")

    model.update()

    # Objective: minimize total cost
    # Cost of x[i,d] = costs[d] * x[i,d]
    obj = gp.quicksum(costs[d] * x[i, d] for (i, d) in x)
    model.setObjective(obj, GRB.MINIMIZE)

    # Constraints: for each month t (0-based), total rented area >= demand[t]
    # A contract starting at month i with duration d+1 covers months i, i+1, ..., i+d
    for t in range(4):
        covering = gp.quicksum(
            x[i, d]
            for (i, d) in x
            if i <= t <= i + d
        )
        model.addConstr(covering >= demand[t], name=f"demand_month_{t+1}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver_status_{model.Status}"}