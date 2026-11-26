import gurobipy as gp
from gurobipy import GRB

def solve(params):
    labor_A = params["labor_A"]
    assembly_B = params["assembly_B"]
    labor_A_heater = params["labor_A_heater"]
    assembly_B_heater = params["assembly_B_heater"]
    inspect_cost_mw = params["inspect_cost_mw"]
    inspect_cost_wh = params["inspect_cost_wh"]
    cap_A = params["cap_A"]
    cap_B = params["cap_B"]
    cost_A = params["cost_A"]
    cost_B = params["cost_B"]
    demand_mw = params["demand_mw"]
    demand_wh = params["demand_wh"]
    inspect_budget = params["inspect_budget"]
    target_mw = params["target_mw"]
    target_wh = params["target_wh"]
    overtime_A_cap = params["overtime_A_cap"]

    model = gp.Model("production_plan")
    model.setParam("OutputFlag", 0)

    # Decision variables: number of microwaves (x1) and water heaters (x2)
    x1 = model.addVar(lb=0, name="x1")  # microwaves
    x2 = model.addVar(lb=0, name="x2")  # water heaters

    # --- Goal programming deviational variables ---

    # Priority 1: Inspection & sales cost <= inspect_budget
    # inspect_cost_mw * x1 + inspect_cost_wh * x2 <= inspect_budget
    # d1m = negative deviation (under), d1p = positive deviation (over)
    d1p = model.addVar(lb=0, name="d1p")
    d1m = model.addVar(lb=0, name="d1m")

    # Priority 2: x1 >= target_mw  =>  x1 + d2m - d2p = target_mw
    d2p = model.addVar(lb=0, name="d2p")
    d2m = model.addVar(lb=0, name="d2m")

    # Priority 3: Full utilization of Workshop A and Workshop B
    # Workshop A: labor_A*x1 + labor_A_heater*x2 = cap_A (with over/under)
    # Workshop B: assembly_B*x1 + assembly_B_heater*x2 = cap_B (with over/under)
    # Weights proportional to hourly costs: w_A = cost_A, w_B = cost_B
    d3Ap = model.addVar(lb=0, name="d3Ap")  # over-utilization A
    d3Am = model.addVar(lb=0, name="d3Am")  # under-utilization A
    d3Bp = model.addVar(lb=0, name="d3Bp")  # over-utilization B
    d3Bm = model.addVar(lb=0, name="d3Bm")  # under-utilization B

    # Priority 4: Workshop A overtime <= overtime_A_cap
    # overtime = max(0, labor_A*x1 + labor_A_heater*x2 - cap_A) = d3Ap
    # d3Ap <= overtime_A_cap  => d3Ap + d4m - d4p = overtime_A_cap
    d4p = model.addVar(lb=0, name="d4p")
    d4m = model.addVar(lb=0, name="d4m")

    # Priority 5: x2 >= target_wh
    d5p = model.addVar(lb=0, name="d5p")
    d5m = model.addVar(lb=0, name="d5m")

    # --- Goal constraints ---

    # Priority 1
    model.addConstr(
        inspect_cost_mw * x1 + inspect_cost_wh * x2 + d1m - d1p == inspect_budget,
        name="goal1"
    )

    # Priority 2
    model.addConstr(
        x1 + d2m - d2p == target_mw,
        name="goal2"
    )

    # Priority 3 - Workshop A utilization
    model.addConstr(
        labor_A * x1 + labor_A_heater * x2 + d3Am - d3Ap == cap_A,
        name="goal3A"
    )

    # Priority 3 - Workshop B utilization
    model.addConstr(
        assembly_B * x1 + assembly_B_heater * x2 + d3Bm - d3Bp == cap_B,
        name="goal3B"
    )

    # Priority 4: Workshop A overtime (d3Ap) should not exceed overtime_A_cap
    model.addConstr(
        d3Ap + d4m - d4p == overtime_A_cap,
        name="goal4"
    )

    # Priority 5
    model.addConstr(
        x2 + d5m - d5p == target_wh,
        name="goal5"
    )

    # Demand ceilings (hard constraints from problem context)
    model.addConstr(x1 <= demand_mw, name="demand_mw")
    model.addConstr(x2 <= demand_wh, name="demand_wh")

    # --- Preemptive (lexicographic) goal programming via weighted sum with large penalties ---
    # We use penalty weights P1 >> P2 >> P3 >> P4 >> P5
    P1 = 1e12
    P2 = 1e9
    P3 = 1e6
    P4 = 1e3
    P5 = 1.0

    # Priority 1: minimize d1p (over inspection budget)
    # Priority 2: minimize d2m (under microwave target)
    # Priority 3: minimize weighted under-utilization of A and B
    #   weight_A proportional to cost_A, weight_B proportional to cost_B
    #   normalize so weights sum to 1 relative to total cost
    total_cost = cost_A + cost_B
    w_A = cost_A / total_cost
    w_B = cost_B / total_cost
    # Priority 4: minimize d4p (overtime exceeds cap)
    # Priority 5: minimize d5m (under water heater target)

    obj = (
        P1 * d1p
        + P2 * d2m
        + P3 * (w_A * d3Am + w_B * d3Bm)
        + P4 * d4p
        + P5 * d5m
    )

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
        return {"objective": None, "status": f"status_{status}"}