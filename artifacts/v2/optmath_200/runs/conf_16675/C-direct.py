import gurobipy as gp
from gurobipy import GRB

def solve(params):
    production_cost = params["production_cost"]
    startup_cost = params["startup_cost"]
    startup_scaling_factor = params["startup_scaling_factor"]
    machine_capacity = params["machine_capacity"]
    holding_cost = params["holding_cost"]      # list of 3
    backlog_cost = params["backlog_cost"]       # list of 3
    demand_period0 = params["demand_period0"]  # list of 3

    num_items = 3
    num_periods = 5
    items = range(num_items)
    periods = range(num_periods)

    # Demands: period 0 from params, periods 1-4 set to 0 (not given)
    demand = {}
    for i in items:
        demand[(i, 0)] = demand_period0[i]
        for t in range(1, num_periods):
            demand[(i, t)] = 0.0

    model = gp.Model("production_planning")
    model.setParam("OutputFlag", 0)

    # Binary: produce item i in period t
    x = model.addVars(num_items, num_periods, vtype=GRB.BINARY, name="x")
    # Binary: startup for item i in period t
    s = model.addVars(num_items, num_periods, vtype=GRB.BINARY, name="s")
    # Continuous: production quantity for item i in period t
    q = model.addVars(num_items, num_periods, lb=0.0, name="q")
    # Continuous: inventory for item i at end of period t
    inv = model.addVars(num_items, num_periods, lb=0.0, name="inv")
    # Continuous: backlog for item i at end of period t
    bl = model.addVars(num_items, num_periods, lb=0.0, name="bl")

    # Objective
    obj = gp.quicksum(
        production_cost * x[i, t]
        + startup_cost * s[i, t]
        + holding_cost[i] * inv[i, t]
        + backlog_cost[i] * bl[i, t]
        for i in items for t in periods
    )
    model.setObjective(obj, GRB.MINIMIZE)

    # Demand balance constraints
    for i in items:
        for t in periods:
            if t == 0:
                # No prior inventory or backlog
                model.addConstr(
                    q[i, t] - demand[(i, t)] == inv[i, t] - bl[i, t],
                    name=f"balance_{i}_{t}"
                )
            else:
                model.addConstr(
                    inv[i, t-1] - bl[i, t-1] + q[i, t] - demand[(i, t)] == inv[i, t] - bl[i, t],
                    name=f"balance_{i}_{t}"
                )

    # Only one item produced per period
    for t in periods:
        model.addConstr(
            gp.quicksum(x[i, t] for i in items) <= 1,
            name=f"one_item_{t}"
        )

    # Production quantity only if item is selected
    for i in items:
        for t in periods:
            model.addConstr(q[i, t] <= machine_capacity * x[i, t], name=f"prod_if_selected_{i}_{t}")

    # Capacity constraint: production + startup_scaling * startup <= machine_capacity
    for t in periods:
        model.addConstr(
            gp.quicksum(q[i, t] + startup_scaling_factor * s[i, t] for i in items) <= machine_capacity,
            name=f"capacity_{t}"
        )

    # Startup logic: s[i,t] = 1 if x[i,t]=1 and x[i,t-1]=0
    for i in items:
        for t in periods:
            if t == 0:
                # At period 0, there's no previous period; startup occurs if produced
                model.addConstr(s[i, t] == x[i, t], name=f"startup_period0_{i}")
            else:
                # s[i,t] >= x[i,t] - x[i,t-1]
                model.addConstr(s[i, t] >= x[i, t] - x[i, t-1], name=f"startup_lb_{i}_{t}")
                # s[i,t] <= x[i,t]
                model.addConstr(s[i, t] <= x[i, t], name=f"startup_ub1_{i}_{t}")
                # s[i,t] <= 1 - x[i,t-1]
                model.addConstr(s[i, t] <= 1 - x[i, t-1], name=f"startup_ub2_{i}_{t}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}