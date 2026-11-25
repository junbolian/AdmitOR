import gurobipy as gp
from gurobipy import GRB

def solve(params):
    W = params["hide_width"]
    H = params["hide_height"]
    pw = params["patch_widths"]   # list of 4 widths
    ph = params["patch_heights"]  # list of 4 heights

    n_patches = 4
    # Upper bound on hides needed is n_patches (one each)
    n_hides = n_patches
    patches = range(n_patches)
    hides = range(n_hides)

    model = gp.Model()
    model.setParam("OutputFlag", 0)
    model.setParam("TimeLimit", 120)

    # a[i][k] = 1 if patch i is assigned to hide k
    a = [[model.addVar(vtype=GRB.BINARY, name=f"a_{i}_{k}")
          for k in hides] for i in patches]

    # x[i], y[i] = bottom-left corner of patch i
    x = [model.addVar(lb=0, ub=W, name=f"x_{i}") for i in patches]
    y = [model.addVar(lb=0, ub=H, name=f"y_{i}") for i in patches]

    # u[k] = 1 if hide k is used
    u = [model.addVar(vtype=GRB.BINARY, name=f"u_{k}") for k in hides]

    # Each patch assigned to exactly one hide
    for i in patches:
        model.addConstr(gp.quicksum(a[i][k] for k in hides) == 1)

    # Hide used if any patch assigned to it
    for i in patches:
        for k in hides:
            model.addConstr(u[k] >= a[i][k])

    # Symmetry breaking: hides used in order
    for k in range(n_hides - 1):
        model.addConstr(u[k] >= u[k + 1])

    # Patch must fit within hide boundaries (big-M: if not on hide k, constraint relaxed)
    M_x = W
    M_y = H
    for i in patches:
        for k in hides:
            # x[i] + pw[i] <= W + M*(1 - a[i][k])
            model.addConstr(x[i] + pw[i] <= W + M_x * (1 - a[i][k]))
            model.addConstr(y[i] + ph[i] <= H + M_y * (1 - a[i][k]))

    # Non-overlap for patches on same hide
    # For each pair (i, j) on same hide k, one of four separation conditions holds
    # Introduce binary vars: d[i][j][k][dir] for each direction
    # dir 0: i left of j, dir 1: j left of i, dir 2: i below j, dir 3: j below i
    pairs = [(i, j) for i in patches for j in patches if i < j]

    for (i, j) in pairs:
        for k in hides:
            # 4 direction binaries
            d = [model.addVar(vtype=GRB.BINARY) for _ in range(4)]
            # At least one direction must be active when both patches on same hide
            # both_on_k <= sum(d); both_on_k = a[i][k] + a[j][k] - 1 (linearized)
            both = model.addVar(vtype=GRB.BINARY)
            model.addConstr(both >= a[i][k] + a[j][k] - 1)
            model.addConstr(both <= a[i][k])
            model.addConstr(both <= a[j][k])
            model.addConstr(gp.quicksum(d) >= both)

            big = W + H  # large enough big-M
            # dir 0: x[i] + pw[i] <= x[j]  =>  x[j] - x[i] >= pw[i]
            model.addConstr(x[j] - x[i] >= pw[i] - big * (1 - d[0]))
            # dir 1: x[j] + pw[j] <= x[i]
            model.addConstr(x[i] - x[j] >= pw[j] - big * (1 - d[1]))
            # dir 2: y[i] + ph[i] <= y[j]
            model.addConstr(y[j] - y[i] >= ph[i] - big * (1 - d[2]))
            # dir 3: y[j] + ph[j] <= y[i]
            model.addConstr(y[i] - y[j] >= ph[j] - big * (1 - d[3]))

    # Objective: minimize number of hides used
    model.setObjective(gp.quicksum(u[k] for k in hides), GRB.MINIMIZE)

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.TIME_LIMIT:
        if model.SolCount > 0:
            return {"objective": float(model.ObjVal), "status": "optimal"}
        return {"objective": None, "status": "time_limit_no_solution"}
    else:
        return {"objective": None, "status": f"gurobi_status_{status}"}