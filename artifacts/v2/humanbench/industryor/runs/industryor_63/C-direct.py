import gurobipy as gp
from gurobipy import GRB

def solve(params):
    profit_A = params["profit_A"]
    profit_B = params["profit_B"]
    profit_target = params["profit_target"]
    time_I_A = params["time_I_A"]
    time_I_B = params["time_I_B"]
    time_II_A = params["time_II_A"]
    time_II_B = params["time_II_B"]
    cap_I = params["cap_I"]
    cap_II = params["cap_II"]
    overtime_cap_II = params["overtime_cap_II"]
    min_A = params["min_A"]
    min_B = params["min_B"]
    overtime_penalty_A = params["overtime_penalty_A"]
    overtime_penalty_B = params["overtime_penalty_B"]

    model = gp.Model("goal_programming")
    model.setParam("OutputFlag", 0)

    # Decision variables: regular production and overtime production in process II
    # x_A, x_B: units produced using regular process II hours
    # y_A, y_B: units produced using overtime process II hours
    x_A = model.addVar(lb=0, name="x_A")
    x_B = model.addVar(lb=0, name="x_B")
    y_A = model.addVar(lb=0, name="y_A")
    y_B = model.addVar(lb=0, name="y_B")

    # Total production
    # total_A = x_A + y_A, total_B = x_B + y_B

    # Goal deviation variables (non-negative)
    # p1: profit >= profit_target
    d1_neg = model.addVar(lb=0, name="d1_neg")  # underachievement of profit goal
    d1_pos = model.addVar(lb=0, name="d1_pos")  # overachievement of profit goal

    # p2: total_A >= min_A
    d2A_neg = model.addVar(lb=0, name="d2A_neg")
    d2A_pos = model.addVar(lb=0, name="d2A_pos")

    # p2: total_B >= min_B
    d2B_neg = model.addVar(lb=0, name="d2B_neg")
    d2B_pos = model.addVar(lb=0, name="d2B_pos")

    # p3a: process I time = cap_I (exactly 150 hours)
    d3_neg = model.addVar(lb=0, name="d3_neg")  # under-utilization of process I
    d3_pos = model.addVar(lb=0, name="d3_pos")  # over-utilization of process I

    # p3b: process II utilization maximized (want to maximize regular + overtime usage)
    # Modeled as: regular II hours + overtime II hours = cap_II + overtime_cap_II (maximize, so minimize underachievement)
    d4_neg = model.addVar(lb=0, name="d4_neg")  # under-utilization of total process II capacity
    d4_pos = model.addVar(lb=0, name="d4_pos")  # over (infeasible by hard constraint, but keep for balance)

    # Hard constraints
    # Process I capacity (hard upper bound)
    model.addConstr(
        time_I_A * (x_A + y_A) + time_I_B * (x_B + y_B) <= cap_I,
        name="process_I_capacity"
    )

    # Regular process II capacity
    model.addConstr(
        time_II_A * x_A + time_II_B * x_B <= cap_II,
        name="process_II_regular_capacity"
    )

    # Overtime process II capacity
    model.addConstr(
        time_II_A * y_A + time_II_B * y_B <= overtime_cap_II,
        name="process_II_overtime_capacity"
    )

    # Goal constraints
    # p1: profit goal
    total_profit = (profit_A * x_A + profit_B * x_B
                    + (profit_A - overtime_penalty_A) * y_A
                    + (profit_B - overtime_penalty_B) * y_B)
    model.addConstr(
        total_profit - d1_pos + d1_neg == profit_target,
        name="goal_profit"
    )

    # p2: minimum production of A
    model.addConstr(
        (x_A + y_A) - d2A_pos + d2A_neg == min_A,
        name="goal_min_A"
    )

    # p2: minimum production of B
    model.addConstr(
        (x_B + y_B) - d2B_pos + d2B_neg == min_B,
        name="goal_min_B"
    )

    # p3a: process I exactly at capacity
    model.addConstr(
        time_I_A * (x_A + y_A) + time_I_B * (x_B + y_B) - d3_pos + d3_neg == cap_I,
        name="goal_process_I_exact"
    )

    # p3b / p4: maximize process II utilization (regular + overtime)
    # Target: use all available cap_II + overtime_cap_II hours
    total_II_capacity = cap_II + overtime_cap_II
    model.addConstr(
        time_II_A * (x_A + y_A) + time_II_B * (x_B + y_B) - d4_pos + d4_neg == total_II_capacity,
        name="goal_process_II_max"
    )

    # Preemptive goal programming via weighted objective with large penalty weights
    # Priority levels: p1 >> p2 >> p3 >> p4
    # Weights: 1e9 for p1, 1e6 for p2, 1e3 for p3, 1 for p4
    # p1: minimize underachievement of profit
    # p2: minimize underachievement of min_A and min_B
    # p3: minimize deviation from exact process I usage (both under and over are penalized equally)
    #     and minimize underachievement of process II utilization
    # p4: minimize underachievement of total process II capacity utilization
    #     (already captured in d4_neg above, but p3b and p4 are separated by priority)

    # p3 has two sub-goals: process I exact (d3_neg + d3_pos) and process II max (d4_neg at p3 level)
    # p4 specifically about overtime usage; since p3 covers maximizing process II including overtime,
    # we treat p3 as minimizing d3_neg + d3_pos (process I exact), and p4 as minimizing d4_neg (process II max)

    w_p1 = 1e9
    w_p2 = 1e6
    w_p3 = 1e3
    w_p4 = 1.0

    model.setObjective(
        w_p1 * d1_neg
        + w_p2 * (d2A_neg + d2B_neg)
        + w_p3 * (d3_neg + d3_pos)
        + w_p4 * d4_neg,
        GRB.MINIMIZE
    )

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