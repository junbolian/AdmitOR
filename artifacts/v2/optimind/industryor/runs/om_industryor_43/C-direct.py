import gurobipy as gp
from gurobipy import GRB

def solve(params):
    prep_A = params["prep_A"]
    prep_B = params["prep_B"]
    prep_C = params["prep_C"]
    labor_A = params["labor_A"]
    labor_B = params["labor_B"]
    labor_C = params["labor_C"]
    material_A = params["material_A"]
    material_B = params["material_B"]
    material_C = params["material_C"]
    tech_capacity = params["tech_capacity"]
    labor_capacity = params["labor_capacity"]
    material_capacity = params["material_capacity"]
    profit_A_tiers = params["profit_A_tiers"]
    profit_B_tiers = params["profit_B_tiers"]
    profit_C_tiers = params["profit_C_tiers"]
    tier_breakpoints_A = params["tier_breakpoints_A"]
    tier_breakpoints_B = params["tier_breakpoints_B"]
    tier_breakpoints_C = params["tier_breakpoints_C"]

    # tier_breakpoints_A: [40, 100, 150]  -> tiers: [0,40], [40,100], [100,150], [150,inf)
    # tier_breakpoints_B: [50, 100]       -> tiers: [0,50], [50,100], [100,inf)
    # tier_breakpoints_C: [100]           -> tiers: [0,100], [100,inf)

    bp_A = tier_breakpoints_A  # list of 3 breakpoints
    bp_B = tier_breakpoints_B  # list of 2 breakpoints
    bp_C = tier_breakpoints_C  # list of 1 breakpoint

    model = gp.Model("production_plan")
    model.setParam("OutputFlag", 0)

    # Segment variables for product A (4 tiers)
    # seg_A[0]: units in [0, bp_A[0]]
    # seg_A[1]: units in [0, bp_A[1]-bp_A[0]]
    # seg_A[2]: units in [0, bp_A[2]-bp_A[1]]
    # seg_A[3]: units in [0, inf)
    seg_A = []
    seg_A.append(model.addVar(lb=0, ub=bp_A[0], name="seg_A0"))
    seg_A.append(model.addVar(lb=0, ub=bp_A[1] - bp_A[0], name="seg_A1"))
    seg_A.append(model.addVar(lb=0, ub=bp_A[2] - bp_A[1], name="seg_A2"))
    seg_A.append(model.addVar(lb=0, name="seg_A3"))

    # Segment variables for product B (3 tiers)
    seg_B = []
    seg_B.append(model.addVar(lb=0, ub=bp_B[0], name="seg_B0"))
    seg_B.append(model.addVar(lb=0, ub=bp_B[1] - bp_B[0], name="seg_B1"))
    seg_B.append(model.addVar(lb=0, name="seg_B2"))

    # Segment variables for product C (2 tiers)
    seg_C = []
    seg_C.append(model.addVar(lb=0, ub=bp_C[0], name="seg_C0"))
    seg_C.append(model.addVar(lb=0, name="seg_C1"))

    # Binary variables to enforce sequential filling of tiers
    # For A: y_A[i]=1 means tier i is fully used (seg_A[i] = its upper bound)
    # We need: seg_A[i+1] > 0 => seg_A[i] = upper_bound(i)
    # Equivalently: seg_A[i] >= upper_bound(i) * y_A[i], seg_A[i+1] <= upper_bound(i+1) * y_A[i]
    # (but seg_A[3] is unbounded, so we just need seg_A[3] <= M * y_A[2])

    y_A = [model.addVar(vtype=GRB.BINARY, name=f"y_A{i}") for i in range(3)]
    y_B = [model.addVar(vtype=GRB.BINARY, name=f"y_B{i}") for i in range(2)]
    y_C = [model.addVar(vtype=GRB.BINARY, name=f"y_C{i}") for i in range(1)]

    # Big-M for unbounded segments: use capacity-based upper bound
    # Total A cannot exceed min(tech_capacity/prep_A, labor_capacity/labor_A, material_capacity/material_A)
    M_A = min(tech_capacity / prep_A, labor_capacity / labor_A, material_capacity / material_A)
    M_B = min(tech_capacity / prep_B, labor_capacity / labor_B, material_capacity / material_B)
    M_C = min(tech_capacity / prep_C, labor_capacity / labor_C, material_capacity / material_C)

    # Sequential tier constraints for A
    # Tier 0 fills before tier 1 starts
    ub_A0 = bp_A[0]
    ub_A1 = bp_A[1] - bp_A[0]
    ub_A2 = bp_A[2] - bp_A[1]

    model.addConstr(seg_A[0] >= ub_A0 * y_A[0], "A_tier0_full")
    model.addConstr(seg_A[1] <= ub_A1 * y_A[0], "A_tier1_needs_y0")
    model.addConstr(seg_A[1] >= ub_A1 * y_A[1], "A_tier1_full")
    model.addConstr(seg_A[2] <= ub_A2 * y_A[1], "A_tier2_needs_y1")
    model.addConstr(seg_A[2] >= ub_A2 * y_A[2], "A_tier2_full")
    model.addConstr(seg_A[3] <= M_A * y_A[2], "A_tier3_needs_y2")

    # Sequential tier constraints for B
    ub_B0 = bp_B[0]
    ub_B1 = bp_B[1] - bp_B[0]

    model.addConstr(seg_B[0] >= ub_B0 * y_B[0], "B_tier0_full")
    model.addConstr(seg_B[1] <= ub_B1 * y_B[0], "B_tier1_needs_y0")
    model.addConstr(seg_B[1] >= ub_B1 * y_B[1], "B_tier1_full")
    model.addConstr(seg_B[2] <= M_B * y_B[1], "B_tier2_needs_y1")

    # Sequential tier constraints for C
    ub_C0 = bp_C[0]

    model.addConstr(seg_C[0] >= ub_C0 * y_C[0], "C_tier0_full")
    model.addConstr(seg_C[1] <= M_C * y_C[0], "C_tier1_needs_y0")

    # Total production quantities
    x_A = gp.quicksum(seg_A)
    x_B = gp.quicksum(seg_B)
    x_C = gp.quicksum(seg_C)

    # Resource constraints
    model.addConstr(prep_A * x_A + prep_B * x_B + prep_C * x_C <= tech_capacity, "tech")
    model.addConstr(labor_A * x_A + labor_B * x_B + labor_C * x_C <= labor_capacity, "labor")
    model.addConstr(material_A * x_A + material_B * x_B + material_C * x_C <= material_capacity, "material")

    # Objective: maximize total profit
    profit_expr = (
        profit_A_tiers[0] * seg_A[0] + profit_A_tiers[1] * seg_A[1] +
        profit_A_tiers[2] * seg_A[2] + profit_A_tiers[3] * seg_A[3] +
        profit_B_tiers[0] * seg_B[0] + profit_B_tiers[1] * seg_B[1] +
        profit_B_tiers[2] * seg_B[2] +
        profit_C_tiers[0] * seg_C[0] + profit_C_tiers[1] * seg_C[1]
    )
    model.setObjective(profit_expr, GRB.MAXIMIZE)

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}