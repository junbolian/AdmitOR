import gurobipy as gp
from gurobipy import GRB

def solve(params):
    demand = {
        1: params["demand_width_1"],
        2: params["demand_width_2"],
        3: params["demand_width_3"],
        4: params["demand_width_4"],
    }

    # yields[p][w] = units of width w produced by pattern p
    yields = {
        0:  {1: params["pattern_0_width_1"],  2: params["pattern_0_width_2"],  3: 0, 4: params["pattern_0_width_4"]},
        1:  {1: params["pattern_1_width_1"],  2: params["pattern_1_width_2"],  3: 0, 4: params["pattern_1_width_4"]},
        2:  {1: 0, 2: 0,                       3: params["pattern_2_width_3"],  4: params["pattern_2_width_4"]},
        3:  {1: params["pattern_3_width_1"],  2: params["pattern_3_width_2"],  3: params["pattern_3_width_3"],  4: params["pattern_3_width_4"]},
        4:  {1: 0, 2: 0,                       3: params["pattern_4_width_3"],  4: params["pattern_4_width_4"]},
        5:  {1: params["pattern_5_width_1"],  2: params["pattern_5_width_2"],  3: params["pattern_5_width_3"],  4: params["pattern_5_width_4"]},
        6:  {1: params["pattern_6_width_1"],  2: params["pattern_6_width_2"],  3: params["pattern_6_width_3"],  4: params["pattern_6_width_4"]},
        7:  {1: params["pattern_7_width_1"],  2: params["pattern_7_width_2"],  3: 0, 4: params["pattern_7_width_4"]},
        8:  {1: params["pattern_8_width_1"],  2: params["pattern_8_width_2"],  3: params["pattern_8_width_3"],  4: params["pattern_8_width_4"]},
        9:  {1: params["pattern_9_width_1"],  2: params["pattern_9_width_2"],  3: params["pattern_9_width_3"],  4: params["pattern_9_width_4"]},
        10: {1: 0, 2: params["pattern_10_width_2"], 3: params["pattern_10_width_3"], 4: params["pattern_10_width_4"]},
        11: {1: 0, 2: params["pattern_11_width_2"], 3: params["pattern_11_width_3"], 4: 0},
    }

    usage_limits = {
        0:  params["usage_limit_0"],
        1:  params["usage_limit_1"],
        2:  params["usage_limit_2"],
        3:  params["usage_limit_3"],
        4:  params["usage_limit_4"],
        5:  params["usage_limit_5"],
        6:  params["usage_limit_6"],
        7:  params["usage_limit_7"],
        8:  params["usage_limit_8"],
        9:  params["usage_limit_9"],
        10: params["usage_limit_10"],
        11: params["usage_limit_11"],
    }

    patterns = list(range(12))
    widths = [1, 2, 3, 4]

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    x = model.addVars(patterns, vtype=GRB.INTEGER, lb=0, name="x")

    for p in patterns:
        model.addConstr(x[p] <= usage_limits[p], name=f"limit_{p}")

    for w in widths:
        model.addConstr(
            gp.quicksum(yields[p][w] * x[p] for p in patterns) >= demand[w],
            name=f"demand_width_{w}"
        )

    model.setObjective(gp.quicksum(x[p] for p in patterns), GRB.MINIMIZE)

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"gurobi_status_{status}"}