import gurobipy as gp
from gurobipy import GRB

def solve(params):
    tech_prep_A = params["tech_prep_A"]
    tech_prep_B = params["tech_prep_B"]
    tech_prep_C = params["tech_prep_C"]
    labor_A = params["labor_A"]
    labor_B = params["labor_B"]
    labor_C = params["labor_C"]
    material_A = params["material_A"]
    material_B = params["material_B"]
    material_C = params["material_C"]
    capacity_tech_prep = params["capacity_tech_prep"]
    capacity_labor = params["capacity_labor"]
    capacity_material = params["capacity_material"]

    profit_A_tier1 = params["profit_A_tier1"]
    profit_A_tier2 = params["profit_A_tier2"]
    profit_A_tier3 = params["profit_A_tier3"]
    profit_A_tier4 = params["profit_A_tier4"]

    profit_B_tier1 = params["profit_B_tier1"]
    profit_B_tier2 = params["profit_B_tier2"]
    profit_B_tier3 = params["profit_B_tier3"]

    profit_C_tier1 = params["profit_C_tier1"]
    profit_C_tier2 = params["profit_C_tier2"]

    bp_A1 = params["breakpoint_A_1"]
    bp_A2 = params["breakpoint_A_2"]
    bp_A3 = params["breakpoint_A_3"]
    bp_B1 = params["breakpoint_B_1"]
    bp_B2 = params["breakpoint_B_2"]
    bp_C1 = params["breakpoint_C_1"]

    model = gp.Model("production_plan")
    model.setParam("OutputFlag", 0)

    # Segment variables for product A (4 tiers)
    # a1 in [0, bp_A1], a2 in [0, bp_A2 - bp_A1], a3 in [0, bp_A3 - bp_A2], a4 in [0, inf)
    a1 = model.addVar(lb=0, ub=bp_A1, name="a1")
    a2 = model.addVar(lb=0, ub=bp_A2 - bp_A1, name="a2")
    a3 = model.addVar(lb=0, ub=bp_A3 - bp_A2, name="a3")
    a4 = model.addVar(lb=0, name="a4")

    # Segment variables for product B (3 tiers)
    b1 = model.addVar(lb=0, ub=bp_B1, name="b1")
    b2 = model.addVar(lb=0, ub=bp_B2 - bp_B1, name="b2")
    b3 = model.addVar(lb=0, name="b3")

    # Segment variables for product C (2 tiers)
    c1 = model.addVar(lb=0, ub=bp_C1, name="c1")
    c2 = model.addVar(lb=0, name="c2")

    # Total production quantities
    total_A = a1 + a2 + a3 + a4
    total_B = b1 + b2 + b3
    total_C = c1 + c2

    # Resource constraints
    model.addConstr(
        tech_prep_A * total_A + tech_prep_B * total_B + tech_prep_C * total_C <= capacity_tech_prep,
        name="tech_prep"
    )
    model.addConstr(
        labor_A * total_A + labor_B * total_B + labor_C * total_C <= capacity_labor,
        name="labor"
    )
    model.addConstr(
        material_A * total_A + material_B * total_B + material_C * total_C <= capacity_material,
        name="material"
    )

    # Piecewise-linear profit: segments fill in order because higher tiers have lower profit.
    # This is enforced naturally by the concave objective maximization.
    # However, to be rigorous, we add ordering constraints:
    # a2 > 0 only if a1 = bp_A1, etc. With concave piecewise linear and maximization,
    # Gurobi will automatically fill lower tiers first. No extra binary variables needed.

    # Objective: maximize total profit
    profit = (
        profit_A_tier1 * a1 + profit_A_tier2 * a2 + profit_A_tier3 * a3 + profit_A_tier4 * a4 +
        profit_B_tier1 * b1 + profit_B_tier2 * b2 + profit_B_tier3 * b3 +
        profit_C_tier1 * c1 + profit_C_tier2 * c2
    )
    model.setObjective(profit, GRB.MAXIMIZE)

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{status}"}