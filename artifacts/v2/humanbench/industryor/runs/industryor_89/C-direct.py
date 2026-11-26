import gurobipy as gp
from gurobipy import GRB

def solve(params):
    remuneration = params["remuneration"]        # list of 6 floats
    max_hours = params["max_hours"]              # 6x5 list of lists
    opening_hours = params["opening_hours"]      # scalar: total hours the lab is open each day
    min_weekly_undergrad = params["min_weekly_undergrad"]  # float
    min_weekly_grad = params["min_weekly_grad"]            # float
    max_shifts_week = params["max_shifts_week"]            # int
    max_students_per_day = params["max_students_per_day"]  # int

    students = range(6)   # 0..5
    days = range(5)       # 0..4 (Mon-Fri)

    model = gp.Model("lab_duty")
    model.setParam("OutputFlag", 0)

    # x[i,d]: hours student i works on day d (continuous)
    x = model.addVars(students, days, lb=0.0, name="x")

    # y[i,d]: binary, 1 if student i has a shift on day d
    y = model.addVars(students, days, vtype=GRB.BINARY, name="y")

    # Objective: minimize total cost
    model.setObjective(
        gp.quicksum(remuneration[i] * x[i, d] for i in students for d in days),
        GRB.MINIMIZE
    )

    # 1. Each day's total hours equals opening_hours (scalar, same for all days)
    for d in days:
        model.addConstr(
            gp.quicksum(x[i, d] for i in students) == opening_hours,
            name=f"opening_{d}"
        )

    # 2. Hours on a day bounded by max availability, and zero if not assigned
    for i in students:
        for d in days:
            model.addConstr(
                x[i, d] <= max_hours[i][d] * y[i, d],
                name=f"max_h_{i}_{d}"
            )

    # 3. Force y=0 when student has zero availability that day
    for i in students:
        for d in days:
            if max_hours[i][d] == 0:
                model.addConstr(y[i, d] == 0, name=f"zero_avail_{i}_{d}")

    # 4. Minimum weekly hours for undergraduates (students 0-3)
    for i in range(4):
        model.addConstr(
            gp.quicksum(x[i, d] for d in days) >= min_weekly_undergrad,
            name=f"min_weekly_ug_{i}"
        )

    # 5. Minimum weekly hours for graduates (students 4-5)
    for i in range(4, 6):
        model.addConstr(
            gp.quicksum(x[i, d] for d in days) >= min_weekly_grad,
            name=f"min_weekly_g_{i}"
        )

    # 6. Each student has at most max_shifts_week shifts per week
    for i in students:
        model.addConstr(
            gp.quicksum(y[i, d] for d in days) <= max_shifts_week,
            name=f"max_shifts_{i}"
        )

    # 7. At most max_students_per_day students assigned per day
    for d in days:
        model.addConstr(
            gp.quicksum(y[i, d] for i in students) <= max_students_per_day,
            name=f"max_students_{d}"
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
        return {"objective": None, "status": f"status_{status}"}