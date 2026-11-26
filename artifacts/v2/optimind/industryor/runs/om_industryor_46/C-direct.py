import gurobipy as gp
from gurobipy import GRB

def solve(params):
    process_I_hours_A = params["process_I_hours_A"]
    process_I_hours_B = params["process_I_hours_B"]
    process_II_hours_A = params["process_II_hours_A"]
    process_II_hours_B = params["process_II_hours_B"]
    capacity_I = params["capacity_I"]
    capacity_II = params["capacity_II"]
    profit_A = params["profit_A"]
    profit_B = params["profit_B"]
    profit_target = params["profit_target"]
    min_units_A = params["min_units_A"]
    min_units_B = params["min_units_B"]
    overtime_reduction_A = params["overtime_reduction_A"]
    overtime_reduction_B = params["overtime_reduction_B"]
    max_overtime_II = params["max_overtime_II"]

    model = gp.Model("microcomputer_production")
    model.setParam("OutputFlag", 0)

    # Decision variables
    # x_A, x_B: units of model A and B produced during regular time in process II
    # x_A_ot, x_B_ot: units of model A and B produced during overtime in process II
    # We split production into regular and overtime portions for process II.
    # Total production: A = x_A + x_A_ot, B = x_B + x_B_ot

    x_A = model.addVar(lb=0, name="x_A")          # units of A in regular time
    x_B = model.addVar(lb=0, name="x_B")          # units of B in regular time
    x_A_ot = model.addVar(lb=0, name="x_A_ot")    # units of A in overtime
    x_B_ot = model.addVar(lb=0, name="x_B_ot")    # units of B in overtime

    # Deviation variables for goal programming
    # p1: profit goal - d1m (under), d1p (over)
    d1m = model.addVar(lb=0, name="d1m")
    d1p = model.addVar(lb=0, name="d1p")

    # p2a: min units A - d2am (under), d2ap (over)
    d2am = model.addVar(lb=0, name="d2am")
    d2ap = model.addVar(lb=0, name="d2ap")

    # p2b: min units B - d2bm (under), d2bp (over)
    d2bm = model.addVar(lb=0, name="d2bm")
    d2bp = model.addVar(lb=0, name="d2bp")

    # p3a: process I fully utilized (exactly capacity_I) - d3am (under), d3ap (over)
    d3am = model.addVar(lb=0, name="d3am")
    d3ap = model.addVar(lb=0, name="d3ap")

    # p3b: process II fully utilized (regular, ideally = capacity_II) - d3bm (under), d3bp (over)
    d3bm = model.addVar(lb=0, name="d3bm")
    d3bp = model.addVar(lb=0, name="d3bp")

    total_A = x_A + x_A_ot
    total_B = x_B + x_B_ot

    # Goal constraints
    # p1: profit >= profit_target
    total_profit = (profit_A * total_A + profit_B * total_B
                    - overtime_reduction_A * x_A_ot
                    - overtime_reduction_B * x_B_ot)
    model.addConstr(total_profit - d1p + d1m == profit_target, "goal_profit")

    # p2a: total_A >= min_units_A
    model.addConstr(total_A - d2ap + d2am == min_units_A, "goal_min_A")

    # p2b: total_B >= min_units_B
    model.addConstr(total_B - d2bp + d2bm == min_units_B, "goal_min_B")

    # p3a: process I usage exactly capacity_I
    model.addConstr(
        process_I_hours_A * total_A + process_I_hours_B * total_B - d3ap + d3am == capacity_I,
        "goal_process_I"
    )

    # p3b: process II regular usage ideally = capacity_II
    model.addConstr(
        process_II_hours_A * x_A + process_II_hours_B * x_B - d3bp + d3bm == capacity_II,
        "goal_process_II"
    )

    # Hard constraint: overtime in process II cannot exceed max_overtime_II
    model.addConstr(
        process_II_hours_A * x_A_ot + process_II_hours_B * x_B_ot <= max_overtime_II,
        "overtime_limit"
    )

    # Lexicographic goal programming via weighted penalty
    # Priority levels: p1 > p2 > p3 > p4
    # p1: minimize d1m (under-achievement of profit target)
    # p2: minimize d2am + d2bm (under-achievement of contract minimums)
    # p3: minimize d3ap (over-use of process I is not allowed since capacity is hard for I,
    #      but here it's a goal), d3am (under-use of process I), d3bm (under-use of process II)
    # p4: minimize overtime usage (already captured by profit reduction)
    # Use large weights to enforce lexicographic ordering
    W1 = 1e9
    W2 = 1e6
    W3 = 1e3

    objective = (
        W1 * d1m
        + W2 * (d2am + d2bm)
        + W3 * (d3am + d3ap + d3bm)
    )

    model.setObjective(objective, GRB.MINIMIZE)
    model.optimize()

    if model.Status == GRB.OPTIMAL:
        # Compute actual profit
        a_val = x_A.X + x_A_ot.X
        b_val = x_B.X + x_B_ot.X
        actual_profit = (profit_A * a_val + profit_B * b_val
                         - overtime_reduction_A * x_A_ot.X
                         - overtime_reduction_B * x_B_ot.X)
        return {"objective": actual_profit, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}