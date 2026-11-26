import gurobipy as gp
from gurobipy import GRB

def solve(params):
    price_A = params["price_A"]
    price_B = params["price_B"]
    hours_manuf_A = params["hours_manuf_A"]
    hours_asm_A = params["hours_asm_A"]
    hours_insp_A = params["hours_insp_A"]
    hours_manuf_B = params["hours_manuf_B"]
    hours_asm_B = params["hours_asm_B"]
    hours_insp_B = params["hours_insp_B"]
    cap_manuf = params["cap_manuf"]
    cap_asm = params["cap_asm"]
    cap_insp = params["cap_insp"]
    cost_manuf = params["cost_manuf"]
    cost_asm = params["cost_asm"]
    cost_insp = params["cost_insp"]
    profit_target = params["profit_target"]
    min_A_target = params["min_A_target"]

    model = gp.Model("motorcycle_goal_programming")
    model.setParam("OutputFlag", 0)

    # Decision variables: production quantities
    x_A = model.addVar(lb=0.0, name="x_A")
    x_B = model.addVar(lb=0.0, name="x_B")

    # Cost per unit
    unit_cost_A = (hours_manuf_A * cost_manuf
                   + hours_asm_A * cost_asm
                   + hours_insp_A * cost_insp)
    unit_cost_B = (hours_manuf_B * cost_manuf
                   + hours_asm_B * cost_asm
                   + hours_insp_B * cost_insp)

    unit_profit_A = price_A - unit_cost_A
    unit_profit_B = price_B - unit_cost_B

    # Goal deviation variables (non-negative)
    # p1: profit >= profit_target
    d1_neg = model.addVar(lb=0.0, name="d1_neg")  # under-achievement of profit
    d1_pos = model.addVar(lb=0.0, name="d1_pos")  # over-achievement of profit

    # p2: x_A >= min_A_target
    d2_neg = model.addVar(lb=0.0, name="d2_neg")  # under-achievement of min_A
    d2_pos = model.addVar(lb=0.0, name="d2_pos")  # over-achievement of min_A

    # p3: minimize idle time for each process (no overtime allowed)
    # idle_manuf = cap_manuf - hours_manuf_A*x_A - hours_manuf_B*x_B >= 0
    # idle_asm   = cap_asm   - hours_asm_A*x_A   - hours_asm_B*x_B   >= 0
    # idle_insp  = cap_insp  - hours_insp_A*x_A  - hours_insp_B*x_B  >= 0
    # Deviation variables for capacity constraints (only underutilization / idle)
    d3_manuf_neg = model.addVar(lb=0.0, name="d3_manuf_neg")  # idle time in manufacturing
    d3_manuf_pos = model.addVar(lb=0.0, name="d3_manuf_pos")  # overtime (must be 0)
    d3_asm_neg = model.addVar(lb=0.0, name="d3_asm_neg")      # idle time in assembly
    d3_asm_pos = model.addVar(lb=0.0, name="d3_asm_pos")      # overtime (must be 0)
    d3_insp_neg = model.addVar(lb=0.0, name="d3_insp_neg")    # idle time in inspection
    d3_insp_pos = model.addVar(lb=0.0, name="d3_insp_pos")    # overtime (must be 0)

    # Goal constraints
    # p1: profit deviation
    model.addConstr(
        unit_profit_A * x_A + unit_profit_B * x_B - d1_pos + d1_neg == profit_target,
        name="goal_profit"
    )

    # p2: min type A production
    model.addConstr(
        x_A - d2_pos + d2_neg == min_A_target,
        name="goal_min_A"
    )

    # p3: capacity usage (no overtime means d_pos must be 0, enforced via constraint)
    model.addConstr(
        hours_manuf_A * x_A + hours_manuf_B * x_B + d3_manuf_neg - d3_manuf_pos == cap_manuf,
        name="goal_manuf"
    )
    model.addConstr(
        hours_asm_A * x_A + hours_asm_B * x_B + d3_asm_neg - d3_asm_pos == cap_asm,
        name="goal_asm"
    )
    model.addConstr(
        hours_insp_A * x_A + hours_insp_B * x_B + d3_insp_neg - d3_insp_pos == cap_insp,
        name="goal_insp"
    )

    # No overtime allowed: force positive deviations (overtime) to zero
    model.addConstr(d3_manuf_pos == 0, name="no_overtime_manuf")
    model.addConstr(d3_asm_pos == 0, name="no_overtime_asm")
    model.addConstr(d3_insp_pos == 0, name="no_overtime_insp")

    # Preemptive goal programming via weighted objective over all goals.
    # Priority structure: p1 >> p2 >> p3
    # Use large penalty weights to encode priority: w_p1 >> w_p2 >> w_p3
    # w_p1 = M^2, w_p2 = M, w_p3 = cost weights (normalized small)
    # M chosen large enough to dominate lower-priority terms.
    big_M1 = 1e8  # priority 1 weight
    big_M2 = 1e4  # priority 2 weight

    # p3 weights are the hourly costs of each process
    obj = (big_M1 * d1_neg
           + big_M2 * d2_neg
           + cost_manuf * d3_manuf_neg
           + cost_asm * d3_asm_neg
           + cost_insp * d3_insp_neg)

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
        return {"objective": None, "status": f"solver_status_{status}"}