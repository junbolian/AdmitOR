import gurobipy as gp
from gurobipy import GRB


def solve(params):
    time_I_A = params["time_I_A"]
    time_I_B = params["time_I_B"]
    time_II_A = params["time_II_A"]
    time_II_B = params["time_II_B"]
    capacity_I = params["capacity_I"]
    capacity_II = params["capacity_II"]
    profit_A = params["profit_A"]
    profit_B = params["profit_B"]
    min_units_A = params["min_units_A"]
    min_units_B = params["min_units_B"]
    target_profit = params["target_profit"]
    target_time_I = params["target_time_I"]
    target_time_II = params["target_time_II"]

    model = gp.Model("microcomputer_goal_programming")
    model.setParam("OutputFlag", 0)

    # Decision variables: production quantities
    x_A = model.addVar(lb=0, name="x_A")
    x_B = model.addVar(lb=0, name="x_B")

    # Goal deviation variables (non-negative)
    # p1: profit goal — d1_neg = underachievement, d1_pos = overachievement
    d1_neg = model.addVar(lb=0, name="d1_neg")
    d1_pos = model.addVar(lb=0, name="d1_pos")

    # p2a: min units of A — d2a_neg = underachievement, d2a_pos = overachievement
    d2a_neg = model.addVar(lb=0, name="d2a_neg")
    d2a_pos = model.addVar(lb=0, name="d2a_pos")

    # p2b: min units of B — d2b_neg = underachievement, d2b_pos = overachievement
    d2b_neg = model.addVar(lb=0, name="d2b_neg")
    d2b_pos = model.addVar(lb=0, name="d2b_pos")

    # p3a: Process I exact time — d3a_neg = under, d3a_pos = over (overtime)
    d3a_neg = model.addVar(lb=0, name="d3a_neg")
    d3a_pos = model.addVar(lb=0, name="d3a_pos")

    # p3b: Process II full utilization — d3b_neg = under, d3b_pos = over (overtime ok)
    d3b_neg = model.addVar(lb=0, name="d3b_neg")
    d3b_pos = model.addVar(lb=0, name="d3b_pos")

    # Goal constraints
    # p1: total profit >= target_profit (minimize d1_neg)
    model.addConstr(
        profit_A * x_A + profit_B * x_B - d1_pos + d1_neg == target_profit,
        name="goal_profit"
    )

    # p2a: x_A >= min_units_A (minimize d2a_neg)
    model.addConstr(
        x_A - d2a_pos + d2a_neg == min_units_A,
        name="goal_min_A"
    )

    # p2b: x_B >= min_units_B (minimize d2b_neg)
    model.addConstr(
        x_B - d2b_pos + d2b_neg == min_units_B,
        name="goal_min_B"
    )

    # p3a: Process I time == target_time_I exactly (minimize both d3a_neg and d3a_pos)
    model.addConstr(
        time_I_A * x_A + time_I_B * x_B - d3a_pos + d3a_neg == target_time_I,
        name="goal_time_I"
    )

    # p3b: Process II fully utilized, overtime allowed (minimize d3b_neg only)
    model.addConstr(
        time_II_A * x_A + time_II_B * x_B - d3b_pos + d3b_neg == target_time_II,
        name="goal_time_II"
    )

    # Hard capacity constraints (cannot exceed available hours without overtime allowance)
    model.addConstr(
        time_I_A * x_A + time_I_B * x_B <= capacity_I,
        name="capacity_I"
    )
    model.addConstr(
        time_II_A * x_A + time_II_B * x_B <= capacity_II,
        name="capacity_II"
    )

    # Objective: maximize total profit
    # Expressed as goal programming with priority weights:
    # Prioritize in order: p1 (profit), p2 (contractual minimums), p3 (process time targets)
    # We minimize a weighted sum of deviations, using large penalty weights for higher priorities,
    # but the primary objective is to maximize profit directly.
    #
    # Since the problem asks to maximize total profit, we maximize profit while penalizing
    # deviations from goals using a preemptive-style weighted objective.
    BIG1 = 1e9  # p1: must not underachieve profit
    BIG2 = 1e6  # p2: contractual minimums
    BIG3 = 1e3  # p3: process time targets

    model.setObjective(
        profit_A * x_A + profit_B * x_B
        - BIG1 * d1_neg
        - BIG2 * (d2a_neg + d2b_neg)
        - BIG3 * (d3a_neg + d3a_pos + d3b_neg),
        GRB.MAXIMIZE
    )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}