import gurobipy as gp
from gurobipy import GRB

def solve(params):
    setup_cost = params["setup_cost"]
    startup_cost = params["startup_cost"]
    capacity = params["capacity"]
    startup_time = params["startup_time"]
    holding_cost = {0: params["holding_cost_P0"], 1: params["holding_cost_P1"]}
    backlog_cost = {0: params["backlog_cost_P0"], 1: params["backlog_cost_P1"]}
    demand = {
        (0, 0): params["demand_P0_P0"],
        (1, 0): params["demand_P1_P0"],
        (0, 1): params["demand_P0_P1"],
        (1, 1): params["demand_P1_P1"],
        (0, 2): params["demand_P0_P2"],
        (1, 2): params["demand_P1_P2"],
    }

    products = [0, 1]
    periods = [0, 1, 2]

    model = gp.Model("lot_sizing")
    model.setParam("OutputFlag", 0)

    # Binary: y[p, t] = 1 if product p is set up (produced) in period t
    y = model.addVars(products, periods, vtype=GRB.BINARY, name="y")
    # Binary: s[p, t] = 1 if machine is started up for product p in period t
    s = model.addVars(products, periods, vtype=GRB.BINARY, name="s")
    # Continuous: x[p, t] = production quantity of product p in period t
    x = model.addVars(products, periods, lb=0.0, name="x")
    # Continuous: inv[p, t] = inventory of product p at end of period t
    inv = model.addVars(products, periods, lb=0.0, name="inv")
    # Continuous: bl[p, t] = backlog of product p at end of period t
    bl = model.addVars(products, periods, lb=0.0, name="bl")

    # Objective
    obj = gp.quicksum(
        setup_cost * y[p, t] + startup_cost * s[p, t]
        + holding_cost[p] * inv[p, t] + backlog_cost[p] * bl[p, t]
        for p in products for t in periods
    )
    model.setObjective(obj, GRB.MINIMIZE)

    # Inventory balance constraints
    for p in products:
        for t in periods:
            if t == 0:
                # No initial inventory or backlog
                model.addConstr(
                    x[p, t] - inv[p, t] + bl[p, t] == demand[p, t],
                    name=f"balance_p{p}_t{t}"
                )
            else:
                model.addConstr(
                    inv[p, t - 1] - bl[p, t - 1] + x[p, t] - inv[p, t] + bl[p, t] == demand[p, t],
                    name=f"balance_p{p}_t{t}"
                )

    # Machine can only produce one product per period
    for t in periods:
        model.addConstr(gp.quicksum(y[p, t] for p in products) <= 1, name=f"one_product_t{t}")

    # Capacity constraints: production + startup_time * startup <= capacity * setup
    for p in products:
        for t in periods:
            model.addConstr(
                x[p, t] + startup_time * s[p, t] <= capacity * y[p, t],
                name=f"capacity_p{p}_t{t}"
            )

    # Startup logic: s[p,t] >= y[p,t] - y[p,t-1]
    # In period 0, startup is required if producing
    for p in products:
        # Period 0: s[p,0] >= y[p,0] (starting from no prior production)
        model.addConstr(s[p, 0] >= y[p, 0], name=f"startup_init_p{p}")
        for t in periods[1:]:
            model.addConstr(s[p, t] >= y[p, t] - y[p, t - 1], name=f"startup_p{p}_t{t}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}