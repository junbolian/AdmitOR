import gurobipy as gp
from gurobipy import GRB

def solve(params):
    min_waitstaff = params["min_waitstaff"]
    # 6 time blocks of 4 hours each, indexed 0..5
    # 0: 2am-6am, 1: 6am-10am, 2: 10am-2pm, 3: 2pm-6pm, 4: 6pm-10pm, 5: 10pm-2am
    # Each shift covers 8 hours = 2 consecutive blocks (wrapping around)
    # Shift i starts at block i and covers blocks i and (i+1) mod 6
    n_blocks = 6

    model = gp.Model("waitstaff_scheduling")
    model.setParam("OutputFlag", 0)

    # x[i] = number of waitstaff starting their 8-hour shift at the beginning of block i
    x = model.addVars(n_blocks, vtype=GRB.INTEGER, lb=0, name="x")

    # Objective: minimize total waitstaff hired
    model.setObjective(gp.quicksum(x[i] for i in range(n_blocks)), GRB.MINIMIZE)

    # Coverage constraints: each block must be covered by shifts starting in that block
    # or the previous block (since each shift covers 2 consecutive blocks)
    for i in range(n_blocks):
        # Block i is covered by shift starting at block i and shift starting at block (i-1) mod 6
        model.addConstr(
            x[i] + x[(i - 1) % n_blocks] >= min_waitstaff[i],
            name=f"coverage_{i}"
        )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}