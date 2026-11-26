import gurobipy as gp
from gurobipy import GRB

def solve(params):
    req_shift1 = params["req_shift1"]
    req_shift2 = params["req_shift2"]
    req_shift3 = params["req_shift3"]
    req_shift4 = params["req_shift4"]
    req_shift5 = params["req_shift5"]
    req_shift6 = params["req_shift6"]

    # x[i] = number of staff starting at the beginning of shift i (i=1..6)
    # Each worker works 8 hours (2 consecutive 4-hour shifts).
    # Shift coverage:
    #   Shift 1 (6-10):  covered by workers starting shift 1 (6-10) or shift 6 (2-6)
    #   Shift 2 (10-14): covered by workers starting shift 1 (6-14) or shift 2 (10-14) -- wait
    #
    # Workers start at beginning of a shift period and work 8 hours = 2 consecutive periods.
    # Start of shift 1 (6:00): works shifts 1 & 2 (6:00-14:00)
    # Start of shift 2 (10:00): works shifts 2 & 3 (10:00-18:00)
    # Start of shift 3 (14:00): works shifts 3 & 4 (14:00-22:00)
    # Start of shift 4 (18:00): works shifts 4 & 5 (18:00-2:00)
    # Start of shift 5 (22:00): works shifts 5 & 6 (22:00-6:00)
    # Start of shift 6 (2:00):  works shifts 6 & 1 (2:00-10:00)
    #
    # Coverage constraints:
    # Shift 1: x1 + x6 >= req_shift1
    # Shift 2: x1 + x2 >= req_shift2
    # Shift 3: x2 + x3 >= req_shift3
    # Shift 4: x3 + x4 >= req_shift4
    # Shift 5: x4 + x5 >= req_shift5
    # Shift 6: x5 + x6 >= req_shift6

    model = gp.Model("bus_crew_scheduling")
    model.setParam("OutputFlag", 0)

    x1 = model.addVar(vtype=GRB.INTEGER, lb=0, name="x1")
    x2 = model.addVar(vtype=GRB.INTEGER, lb=0, name="x2")
    x3 = model.addVar(vtype=GRB.INTEGER, lb=0, name="x3")
    x4 = model.addVar(vtype=GRB.INTEGER, lb=0, name="x4")
    x5 = model.addVar(vtype=GRB.INTEGER, lb=0, name="x5")
    x6 = model.addVar(vtype=GRB.INTEGER, lb=0, name="x6")

    model.setObjective(x1 + x2 + x3 + x4 + x5 + x6, GRB.MINIMIZE)

    model.addConstr(x1 + x6 >= req_shift1, name="cov_shift1")
    model.addConstr(x1 + x2 >= req_shift2, name="cov_shift2")
    model.addConstr(x2 + x3 >= req_shift3, name="cov_shift3")
    model.addConstr(x3 + x4 >= req_shift4, name="cov_shift4")
    model.addConstr(x4 + x5 >= req_shift5, name="cov_shift5")
    model.addConstr(x5 + x6 >= req_shift6, name="cov_shift6")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver_status_{model.Status}"}