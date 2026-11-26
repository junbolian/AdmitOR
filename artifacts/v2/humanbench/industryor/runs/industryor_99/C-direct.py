import gurobipy as gp
from gurobipy import GRB

def solve(params):
    prod_time_hours = params["prod_time_hours"]
    rate_m_per_hour = params["rate_m_per_hour"]
    curtain_demand_m = params["curtain_demand_m"]
    clothing_demand_m = params["clothing_demand_m"]
    curtain_profit_per_m = params["curtain_profit_per_m"]
    clothing_profit_per_m = params["clothing_profit_per_m"]
    overtime_cap_hours = params["overtime_cap_hours"]

    model = gp.Model("textile_goal_programming")
    model.setParam("OutputFlag", 0)

    # Decision variables: meters of curtain fabric (x1) and clothing fabric (x2)
    x1 = model.addVar(lb=0, name="x1_curtain")
    x2 = model.addVar(lb=0, name="x2_clothing")

    # Deviation variables for each goal (negative = under, positive = over)
    # Goal 1: total production time = prod_time_hours (use full 80 hours)
    d1_neg = model.addVar(lb=0, name="d1_neg")  # underachievement (< 80h)
    d1_pos = model.addVar(lb=0, name="d1_pos")  # overachievement (> 80h = overtime)

    # Goal 2: overtime <= overtime_cap_hours
    # overtime = d1_pos, so d1_pos - d2_pos <= overtime_cap_hours
    # We model: d1_pos = overtime_cap_hours + d2_neg - d2_pos
    # Simpler: introduce d2_pos as excess overtime beyond cap
    d2_pos = model.addVar(lb=0, name="d2_pos")  # overtime exceeding cap

    # Goal 3: curtain sales >= curtain_demand_m, clothing sales >= clothing_demand_m
    # weighted by profit
    d3a_neg = model.addVar(lb=0, name="d3a_neg")  # curtain underachievement
    d3a_pos = model.addVar(lb=0, name="d3a_pos")  # curtain overachievement
    d3b_neg = model.addVar(lb=0, name="d3b_neg")  # clothing underachievement
    d3b_pos = model.addVar(lb=0, name="d3b_pos")  # clothing overachievement

    # Goal 4: minimize overtime (d1_pos)
    # d1_pos already defined above

    # --- Constraints ---

    # Production time constraint:
    # (x1 + x2) / rate_m_per_hour = prod_time_hours + d1_pos - d1_neg
    # i.e., x1 + x2 = rate_m_per_hour * prod_time_hours + rate_m_per_hour * (d1_pos - d1_neg)
    # Rearranged: (x1 + x2) / rate_m_per_hour - d1_pos + d1_neg = prod_time_hours
    model.addConstr(
        (x1 + x2) / rate_m_per_hour - d1_pos + d1_neg == prod_time_hours,
        name="goal1_time"
    )

    # Goal 2: overtime (d1_pos) <= overtime_cap_hours
    # d1_pos - d2_pos <= overtime_cap_hours  =>  d1_pos - d2_pos + d2_neg = overtime_cap_hours
    # We only care about excess, so: d2_pos = max(0, d1_pos - overtime_cap_hours)
    # Model as: d1_pos - d2_pos <= overtime_cap_hours
    model.addConstr(d1_pos - d2_pos <= overtime_cap_hours, name="goal2_overtime_cap")

    # Goal 3a: curtain sales >= curtain_demand_m
    model.addConstr(x1 - d3a_pos + d3a_neg == curtain_demand_m, name="goal3a_curtain")

    # Goal 3b: clothing sales >= clothing_demand_m
    model.addConstr(x2 - d3b_pos + d3b_neg == clothing_demand_m, name="goal3b_clothing")

    # Sales cannot exceed demand (fabric is made to order up to demand)
    model.addConstr(x1 <= curtain_demand_m, name="curtain_max")
    model.addConstr(x2 <= clothing_demand_m, name="clothing_max")

    # --- Lexicographic / weighted goal objective ---
    # Priority structure: p1 >> p2 >> p3 >> p4
    # We use large penalty weights to approximate lexicographic ordering.
    # Assign weights: p1=1e9, p2=1e6, p3=profit-weighted, p4=1
    # p1: minimize d1_neg (don't underuse time) — overuse is handled by p2/p4
    # p2: minimize d2_pos (overtime beyond cap)
    # p3: minimize profit-weighted underachievement of demands
    #     weight for curtain: curtain_profit_per_m, for clothing: clothing_profit_per_m
    # p4: minimize d1_pos (overtime hours)

    w_p1 = 1e9
    w_p2 = 1e6
    w_p4 = 1.0

    model.setObjective(
        w_p1 * d1_neg
        + w_p2 * d2_pos
        + curtain_profit_per_m * d3a_neg + clothing_profit_per_m * d3b_neg
        + w_p4 * d1_pos,
        GRB.MINIMIZE
    )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver_status_{model.Status}"}