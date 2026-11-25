import gurobipy as gp
from gurobipy import GRB


def solve(params):
    W = params["hide_width"]
    H = params["hide_height"]
    pw = params["patch_widths"]   # list of 4 widths
    ph = params["patch_heights"]  # list of 4 heights

    n_patches = 4
    patches = range(n_patches)

    # Upper bound on hides needed: each patch on its own hide
    max_hides = n_patches
    hides = range(max_hides)

    model = gp.Model()
    model.setParam("OutputFlag", 0)
    model.setParam("TimeLimit", 120)

    # z[k] = 1 if hide k is used
    z = model.addVars(max_hides, vtype=GRB.BINARY, name="z")

    # a[i][k] = 1 if patch i is assigned to hide k
    a = model.addVars(n_patches, max_hides, vtype=GRB.BINARY, name="a")

    # x[i], y[i] = bottom-left corner of patch i
    x = model.addVars(n_patches, lb=0.0, name="x")
    y = model.addVars(n_patches, lb=0.0, name="y")

    # Objective: minimize number of hides used
    model.setObjective(gp.quicksum(z[k] for k in hides), GRB.MINIMIZE)

    # Each patch assigned to exactly one hide
    for i in patches:
        model.addConstr(gp.quicksum(a[i, k] for k in hides) == 1)

    # If patch i on hide k, it must fit within hide boundaries
    # x[i] + pw[i] <= W + (1 - a[i,k]) * M  =>  x[i] + pw[i] - W <= (1-a[i,k])*M
    # We use big-M = max(W, H)
    M_bound = max(W, H)

    for i in patches:
        for k in hides:
            model.addConstr(x[i] + pw[i] <= W + M_bound * (1 - a[i, k]))
            model.addConstr(y[i] + ph[i] <= H + M_bound * (1 - a[i, k]))

    # If a hide is used by any patch, z[k] = 1
    for k in hides:
        for i in patches:
            model.addConstr(z[k] >= a[i, k])

    # Break symmetry: hides used in order
    for k in range(max_hides - 1):
        model.addConstr(z[k] >= z[k + 1])

    # Non-overlap constraints for patches on the same hide
    # For each pair (i, j), i < j: if both on same hide k, they must not overlap.
    # Overlap in 2D: one of four separation conditions must hold:
    #   i is left of j:  x[i] + pw[i] <= x[j]
    #   i is right of j: x[j] + pw[j] <= x[i]
    #   i is below j:    y[i] + ph[i] <= y[j]
    #   i is above j:    y[j] + ph[j] <= y[i]
    #
    # Introduce binary d[i,j,r] for r in {0,1,2,3}: which separation applies
    # sum of d[i,j,r] >= 1 when both on same hide

    pairs = [(i, j) for i in patches for j in patches if i < j]
    d = model.addVars(
        [(i, j, r) for (i, j) in pairs for r in range(4)],
        vtype=GRB.BINARY,
        name="d"
    )

    for (i, j) in pairs:
        for k in hides:
            # both_on_k is implied when a[i,k] + a[j,k] = 2
            # We need: sum_r d[i,j,r] >= a[i,k] + a[j,k] - 1
            model.addConstr(
                gp.quicksum(d[i, j, r] for r in range(4)) >= a[i, k] + a[j, k] - 1
            )

        # Separation constraints with big-M
        # r=0: x[i] + pw[i] <= x[j]
        model.addConstr(x[i] + pw[i] <= x[j] + M_bound * (1 - d[i, j, 0]))
        # r=1: x[j] + pw[j] <= x[i]
        model.addConstr(x[j] + pw[j] <= x[i] + M_bound * (1 - d[i, j, 1]))
        # r=2: y[i] + ph[i] <= y[j]
        model.addConstr(y[i] + ph[i] <= y[j] + M_bound * (1 - d[i, j, 2]))
        # r=3: y[j] + ph[j] <= y[i]
        model.addConstr(y[j] + ph[j] <= y[i] + M_bound * (1 - d[i, j, 3]))

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL or (status == GRB.TIME_LIMIT and model.SolCount > 0):
        obj_val = float(model.ObjVal)
        label = "optimal" if status == GRB.OPTIMAL else "time_limit_feasible"
        return {"objective": obj_val, "status": label}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.TIME_LIMIT:
        return {"objective": None, "status": "time_limit_no_solution"}
    else:
        return {"objective": None, "status": f"gurobi_status_{status}"}