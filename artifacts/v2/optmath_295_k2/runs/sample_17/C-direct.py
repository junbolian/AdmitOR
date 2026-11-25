import gurobipy as gp
from gurobipy import GRB

def solve(params):
    demand_w1 = params["demand_width_1"]
    demand_w2 = params["demand_width_2"]
    demand_w3 = params["demand_width_3"]
    demand_w4 = params["demand_width_4"]

    # Pattern yields: patterns x widths (0 if not produced)
    yields = {
        (0, 1): params["pattern_0_width_1"],
        (0, 2): params["pattern_0_width_2"],
        (0, 4): params["pattern_0_width_4"],
        (1, 1): params["pattern_1_width_1"],
        (1, 2): params["pattern_1_width_2"],
        (1, 4): params["pattern_1_width_4"],
        (2, 3): params["pattern_2_width_3"],
        (2, 4): params["pattern_2_width_4"],
        (3, 1): params["pattern_3_width_1"],
        (3, 2): params["pattern_3_width_2"],
        (3, 3): params["pattern_3_width_3"],
        (3, 4): params["pattern_3_width_4"],
        (4, 3): params["pattern_4_width_3"],
        (4, 4): params["pattern_4_width_4"],
        (5, 1): params["pattern_5_width_1"],
        (5, 2): params["pattern_5_width_2"],
        (5, 3): params["pattern_5_width_3"],
        (5, 4): params["pattern_5_width_4"],
        (6, 1): params["pattern_6_width_1"],
        (6, 2): params["pattern_6_width_2"],
        (6, 3): params["pattern_6_width_3"],
        (6, 4): params["pattern_6_width_4"],
        (7, 1): params["pattern_7_width_1"],
        (7, 2): params["pattern_7_width_2"],
        (7, 4): params["pattern_7_width_4"],
        (8, 1): params["pattern_8_width_1"],
        (8, 2): params["pattern_8_width_2"],
        (8, 3): params["pattern_8_width_3"],
        (8, 4): params["pattern_8_width_4"],
        (9, 1): params["pattern_9_width_1"],
        (9, 2): params["pattern_9_width_2"],
        (9, 3): params["pattern_9_width_3"],
        (9, 4): params["pattern_9_width_4"],
        (10, 2): params["pattern_10_width_2"],
        (10, 3): params["pattern_10_width_3"],
        (10, 4): params["pattern_10_width_4"],
        (11, 2): params["pattern_11_width_2"],
        (11, 3): params["pattern_11_width_3"],
    }

    usage_limits = [params[f"usage_limit_{p}"] for p in range(12)]

    num_patterns = 12
    patterns = range(num_patterns)

    model = gp.Model("cutting_stock")
    model.setParam("OutputFlag", 0)

    x = model.addVars(num_patterns, vtype=GRB.INTEGER, lb=0, name="x")

    # Usage limit constraints
    for p in patterns:
        model.addConstr(x[p] <= usage_limits[p], name=f"limit_{p}")

    # Demand constraints for each width
    def pattern_yield(p, w):
        return yields.get((p, w), 0)

    model.addConstr(
        gp.quicksum(pattern_yield(p, 1) * x[p] for p in patterns) >= demand_w1,
        name="demand_w1"
    )
    model.addConstr(
        gp.quicksum(pattern_yield(p, 2) * x[p] for p in patterns) >= demand_w2,
        name="demand_w2"
    )
    model.addConstr(
        gp.quicksum(pattern_yield(p, 3) * x[p] for p in patterns) >= demand_w3,
        name="demand_w3"
    )
    model.addConstr(
        gp.quicksum(pattern_yield(p, 4) * x[p] for p in patterns) >= demand_w4,
        name="demand_w4"
    )

    # Minimize total rolls used
    model.setObjective(gp.quicksum(x[p] for p in patterns), GRB.MINIMIZE)

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.INF_OR_UNBD:
        return {"objective": None, "status": "infeasible_or_unbounded"}
    else:
        return {"objective": None, "status": f"solver_status_{model.Status}"}