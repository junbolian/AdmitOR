import gurobipy as gp
from gurobipy import GRB

def solve(params):
    demand_2_6   = params["demand_2_6"]
    demand_6_10  = params["demand_6_10"]
    demand_10_14 = params["demand_10_14"]
    demand_14_18 = params["demand_14_18"]
    demand_18_22 = params["demand_18_22"]
    demand_22_2  = params["demand_22_2"]

    # Shift start times and coverage:
    # x0: starts 2:00,  covers 2-6, 6-10
    # x1: starts 6:00,  covers 6-10, 10-14
    # x2: starts 10:00, covers 10-14, 14-18
    # x3: starts 14:00, covers 14-18, 18-22
    # x4: starts 18:00, covers 18-22, 22-2
    # x5: starts 22:00, covers 22-2, 2-6

    model = gp.Model("convenience_store_staffing")
    model.setParam("OutputFlag", 0)

    x0 = model.addVar(vtype=GRB.INTEGER, lb=0, name="x0")  # starts 2:00
    x1 = model.addVar(vtype=GRB.INTEGER, lb=0, name="x1")  # starts 6:00
    x2 = model.addVar(vtype=GRB.INTEGER, lb=0, name="x2")  # starts 10:00
    x3 = model.addVar(vtype=GRB.INTEGER, lb=0, name="x3")  # starts 14:00
    x4 = model.addVar(vtype=GRB.INTEGER, lb=0, name="x4")  # starts 18:00
    x5 = model.addVar(vtype=GRB.INTEGER, lb=0, name="x5")  # starts 22:00

    model.setObjective(x0 + x1 + x2 + x3 + x4 + x5, GRB.MINIMIZE)

    # Period 2:00-6:00: covered by shifts starting 2:00 (x0) and 22:00 (x5)
    model.addConstr(x0 + x5 >= demand_2_6, name="c_2_6")

    # Period 6:00-10:00: covered by shifts starting 2:00 (x0) and 6:00 (x1)
    model.addConstr(x0 + x1 >= demand_6_10, name="c_6_10")

    # Period 10:00-14:00: covered by shifts starting 6:00 (x1) and 10:00 (x2)
    model.addConstr(x1 + x2 >= demand_10_14, name="c_10_14")

    # Period 14:00-18:00: covered by shifts starting 10:00 (x2) and 14:00 (x3)
    model.addConstr(x2 + x3 >= demand_14_18, name="c_14_18")

    # Period 18:00-22:00: covered by shifts starting 14:00 (x3) and 18:00 (x4)
    model.addConstr(x3 + x4 >= demand_18_22, name="c_18_22")

    # Period 22:00-2:00: covered by shifts starting 18:00 (x4) and 22:00 (x5)
    model.addConstr(x4 + x5 >= demand_22_2, name="c_22_2")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}