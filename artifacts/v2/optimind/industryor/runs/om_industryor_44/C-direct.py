import gurobipy as gp
from gurobipy import GRB

def solve(params):
    wage = params["wage"]                          # list of 6 wages, index 0..5 -> students 1..6
    max_hours = params["max_hours"]                # 6x5 matrix, max_hours[i][d] for student i+1, day d+1
    daily_op = params["daily_operation_hours"]     # scalar: lab open hours per day (e.g. 14)
    undergrad_min = params["undergrad_min_hours"]  # scalar: min weekly hours for undergrads
    grad_min = params["grad_min_hours"]            # scalar: min weekly hours for grads
    max_shifts = params["max_shifts_per_student"]  # scalar: max shifts per student per week
    max_students_day = params["max_students_per_day"]  # scalar: max distinct students per day

    num_students = 6
    num_days = 5
    students = range(num_students)   # 0..5
    days = range(num_days)           # 0..4

    # undergrads: students 0..3 (1-indexed: 1..4)
    # grads: students 4..5 (1-indexed: 5..6)
    undergrads = range(4)
    grads = range(4, 6)

    model = gp.Model("lab_scheduling")
    model.setParam("OutputFlag", 0)

    # h[i][d]: hours student i works on day d
    h = [[model.addVar(lb=0.0, name=f"h_{i}_{d}") for d in days] for i in students]

    # y[i][d]: binary, 1 if student i works on day d (at least 1 shift = positive hours)
    y = [[model.addVar(vtype=GRB.BINARY, name=f"y_{i}_{d}") for d in days] for i in students]

    # Objective: minimize total wage cost
    model.setObjective(
        gp.quicksum(wage[i] * h[i][d] for i in students for d in days),
        GRB.MINIMIZE
    )

    # 1. Total hours each day must equal daily operation hours (exactly one student on duty at all times)
    for d in days:
        model.addConstr(
            gp.quicksum(h[i][d] for i in students) == daily_op,
            name=f"coverage_{d}"
        )

    # 2. Hours for student i on day d cannot exceed their max available hours
    for i in students:
        for d in days:
            model.addConstr(h[i][d] <= max_hours[i][d] * y[i][d], name=f"max_avail_{i}_{d}")
            model.addConstr(h[i][d] <= max_hours[i][d], name=f"max_cap_{i}_{d}")

    # 3. Link y to h: if y[i][d]=0 then h[i][d]=0
    #    (already enforced by max_avail; also need h[i][d] >= 0 which is the lb)
    #    Force y=1 only if h>0: use h[i][d] >= epsilon * y[i][d] but we use big-M the other direction
    #    Actually we need y[i][d]=1 iff h[i][d]>0 for the shifts constraint.
    #    h[i][d] >= y[i][d] * small_epsilon would be strict, but since hours are integers in spirit
    #    we use: h[i][d] >= y[i][d] (at least 1 hour if scheduled)
    for i in students:
        for d in days:
            model.addConstr(h[i][d] >= y[i][d], name=f"min_shift_hour_{i}_{d}")

    # 4. Minimum weekly hours
    for i in undergrads:
        model.addConstr(
            gp.quicksum(h[i][d] for d in days) >= undergrad_min,
            name=f"min_weekly_undergrad_{i}"
        )
    for i in grads:
        model.addConstr(
            gp.quicksum(h[i][d] for d in days) >= grad_min,
            name=f"min_weekly_grad_{i}"
        )

    # 5. Max shifts per student per week
    for i in students:
        model.addConstr(
            gp.quicksum(y[i][d] for d in days) <= max_shifts,
            name=f"max_shifts_{i}"
        )

    # 6. Max distinct students per day
    for d in days:
        model.addConstr(
            gp.quicksum(y[i][d] for i in students) <= max_students_day,
            name=f"max_students_day_{d}"
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