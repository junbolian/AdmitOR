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

    # If patch i is on hide k, it must fit within hide boundaries
    # x[i] + pw[i] <= W * (1 - a[i,k]) + W  =>  x[i] + pw[i] <= W when a[i,k]=1
    # We encode: x[i] + pw[i] <= W + W*(1 - a[i,k])  (big-M with M=W)
    for i in patches:
        for k in hides:
            model.addConstr(x[i] + pw[i] <= W + W * (1 - a[i, k]))
            model.addConstr(y[i] + ph[i] <= H + H * (1 - a[i, k]))
            model.addConstr(x[i] >= 0)
            model.addConstr(y[i] >= 0)

    # If patch i is on hide k, hide k must be active
    for i in patches:
        for k in hides:
            model.addConstr(a[i, k] <= z[k])

    # Symmetry breaking: hides used in order
    for k in range(max_hides - 1):
        model.addConstr(z[k] >= z[k + 1])

    # Non-overlap: for each pair of patches on the same hide, at least one separation holds
    # For patches i and j on hide k: one of four conditions must hold
    # We use binary vars to select which separation applies
    # b[i,j,k,d]: separation direction d for pair (i,j) on hide k
    # d=0: i left of j,  d=1: j left of i,  d=2: i below j,  d=3: j below i

    pairs = [(i, j) for i in patches for j in patches if i < j]

    # on_same[i,j,k] = 1 if both patch i and j are on hide k
    on_same = model.addVars(
        [(i, j, k) for (i, j) in pairs for k in hides],
        vtype=GRB.BINARY, name="on_same"
    )

    # sep[i,j,d] = 1 if separation direction d is chosen for pair (i,j)
    sep = model.addVars(
        [(i, j, d) for (i, j) in pairs for d in range(4)],
        vtype=GRB.BINARY, name="sep"
    )

    big_M_x = W
    big_M_y = H

    for (i, j) in pairs:
        # on_same[i,j,k] = a[i,k] AND a[j,k]
        for k in hides:
            model.addConstr(on_same[i, j, k] <= a[i, k])
            model.addConstr(on_same[i, j, k] <= a[j, k])
            model.addConstr(on_same[i, j, k] >= a[i, k] + a[j, k] - 1)

        # Total "same hide" indicator
        same_ij = gp.quicksum(on_same[i, j, k] for k in hides)

        # At least one separation direction must hold when they share a hide
        model.addConstr(gp.quicksum(sep[i, j, d] for d in range(4)) >= same_ij)

        # Separation constraints (always valid via big-M when sep=0)
        # d=0: x[i] + pw[i] <= x[j]
        model.addConstr(x[i] + pw[i] <= x[j] + big_M_x * (1 - sep[i, j, 0]))
        # d=1: x[j] + pw[j] <= x[i]
        model.addConstr(x[j] + pw[j] <= x[i] + big_M_x * (1 - sep[i, j, 1]))
        # d=2: y[i] + ph[i] <= y[j]
        model.addConstr(y[i] + ph[i] <= y[j] + big_M_y * (1 - sep[i, j, 2]))
        # d=3: y[j] + ph[j] <= y[i]
        model.addConstr(y[j] + ph[j] <= y[i] + big_M_y * (1 - sep[i, j, 3]))

    model.optimize()

    status = model.Status
    if status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    if status == GRB.TIME_LIMIT and model.SolCount == 0:
        return {"objective": None, "status": "time_limit_no_solution"}
    if model.SolCount == 0:
        return {"objective": None, "status": "no_solution"}

    return {
        "objective": float(model.ObjVal),
        "status": "optimal"
    }