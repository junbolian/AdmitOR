import gurobipy as gp
from gurobipy import GRB

def solve(params):
    man_hours_A = params["man_hours_A"]
    man_hours_B = params["man_hours_B"]
    asm_hours_A = params["asm_hours_A"]
    asm_hours_B = params["asm_hours_B"]
    insp_hours_A = params["insp_hours_A"]
    insp_hours_B = params["insp_hours_B"]
    price_A = params["price_A"]
    price_B = params["price_B"]
    cap_manufacturing = params["cap_manufacturing"]
    cap_assembly = params["cap_assembly"]
    cap_inspection = params["cap_inspection"]
    cost_manufacturing = params["cost_manufacturing"]
    cost_assembly = params["cost_assembly"]
    cost_inspection = params["cost_inspection"]
    profit_goal = params["profit_goal"]
    min_A_goal = params["min_A_goal"]

    # Compute profit per unit (selling price minus production costs)
    profit_A = (price_A
                - man_hours_A * cost_manufacturing
                - asm_hours_A * cost_assembly
                - insp_hours_A * cost_inspection)
    profit_B = (price_B
                - man_hours_B * cost_manufacturing
                - asm_hours_B * cost_assembly
                - insp_hours_B * cost_inspection)

    model = gp.Model("goal_programming_motorcycles")
    model.setParam("OutputFlag", 0)

    # Decision variables: units of Type A and Type B produced
    x_A = model.addVar(lb=0.0, name="x_A")
    x_B = model.addVar(lb=0.0, name="x_B")

    # Goal deviation variables (non-negative)
    # Goal 1: profit >= profit_goal  =>  profit_A*x_A + profit_B*x_B + d1_neg - d1_pos = profit_goal
    d1_neg = model.addVar(lb=0.0, name="d1_neg")  # underachievement (bad)
    d1_pos = model.addVar(lb=0.0, name="d1_pos")  # overachievement (fine)

    # Goal 2: x_A >= min_A_goal  =>  x_A + d2_neg - d2_pos = min_A_goal
    d2_neg = model.addVar(lb=0.0, name="d2_neg")  # underachievement (bad)
    d2_pos = model.addVar(lb=0.0, name="d2_pos")  # overachievement (fine)

    # Goal 3: minimize idle time in each process (no overtime => only d3x_neg matters as idle,
    #         and we penalize underutilization weighted by hourly cost; no overtime means d3x_pos = 0 is desired)
    # Manufacturing: man_hours_A*x_A + man_hours_B*x_B + d3m_neg - d3m_pos = cap_manufacturing
    d3m_neg = model.addVar(lb=0.0, name="d3m_neg")  # idle manufacturing hours
    d3m_pos = model.addVar(lb=0.0, name="d3m_pos")  # overtime manufacturing (to be zeroed by constraint)

    # Assembly: asm_hours_A*x_A + asm_hours_B*x_B + d3a_neg - d3a_pos = cap_assembly
    d3a_neg = model.addVar(lb=0.0, name="d3a_neg")  # idle assembly hours
    d3a_pos = model.addVar(lb=0.0, name="d3a_pos")  # overtime assembly

    # Inspection: insp_hours_A*x_A + insp_hours_B*x_B + d3i_neg - d3i_pos = cap_inspection
    d3i_neg = model.addVar(lb=0.0, name="d3i_neg")  # idle inspection hours
    d3i_pos = model.addVar(lb=0.0, name="d3i_pos")  # overtime inspection

    # Goal constraints
    model.addConstr(
        profit_A * x_A + profit_B * x_B + d1_neg - d1_pos == profit_goal,
        name="goal_profit"
    )
    model.addConstr(
        x_A + d2_neg - d2_pos == min_A_goal,
        name="goal_min_A"
    )
    model.addConstr(
        man_hours_A * x_A + man_hours_B * x_B + d3m_neg - d3m_pos == cap_manufacturing,
        name="goal_manufacturing"
    )
    model.addConstr(
        asm_hours_A * x_A + asm_hours_B * x_B + d3a_neg - d3a_pos == cap_assembly,
        name="goal_assembly"
    )
    model.addConstr(
        insp_hours_A * x_A + insp_hours_B * x_B + d3i_neg - d3i_pos == cap_inspection,
        name="goal_inspection"
    )

    # No overtime hard constraints (p3: no overtime allowed)
    model.addConstr(d3m_pos == 0.0, name="no_overtime_manufacturing")
    model.addConstr(d3a_pos == 0.0, name="no_overtime_assembly")
    model.addConstr(d3i_pos == 0.0, name="no_overtime_inspection")

    # Preemptive goal programming via weighted objective over priorities.
    # We use a large-M weighting approach to encode lexicographic priorities:
    #   p1 >> p2 >> p3
    # Weights: M^2 for p1, M for p2, 1 for p3 (M large enough to separate priorities).
    # p1: minimize d1_neg (profit underachievement)
    # p2: minimize d2_neg (Type A underproduction)
    # p3: minimize weighted idle time (cost_manufacturing*d3m_neg + cost_assembly*d3a_neg + cost_inspection*d3i_neg)
    big_M = 1e6

    obj = (big_M * big_M * d1_neg
           + big_M * d2_neg
           + cost_manufacturing * d3m_neg
           + cost_assembly * d3a_neg
           + cost_inspection * d3i_neg)

    model.setObjective(obj, GRB.MINIMIZE)
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