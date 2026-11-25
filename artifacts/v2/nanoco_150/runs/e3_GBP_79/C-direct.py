import gurobipy as gp
from gurobipy import GRB


def solve(params):
    sheet_width = params["sheet_width"]
    sheet_length = params["sheet_length"]
    bw = list(params["billboard_widths"])
    bh = list(params["billboard_heights"])
    n = len(bw)
    K = n  # upper bound on number of sheets: one sheet per billboard

    model = gp.Model("billboard_packing")
    model.Params.OutputFlag = 0

    # A billboard that does not fit within a single sheet makes the whole
    # problem infeasible (no splitting allowed).
    for i in range(n):
        if bw[i] > sheet_width or bh[i] > sheet_length:
            return {"objective": None, "status": "infeasible_billboard_too_large"}

    # Assignment: a[i,k] = 1 if billboard i is placed on sheet k.
    a = model.addVars(n, K, vtype=GRB.BINARY, name="a")
    # Sheet usage: z[k] = 1 if sheet k carries at least one billboard.
    z = model.addVars(K, vtype=GRB.BINARY, name="z")
    # Bottom-left corner position of each billboard within its sheet.
    x = model.addVars(n, lb=0.0, ub=sheet_width, name="x")
    y = model.addVars(n, lb=0.0, ub=sheet_length, name="y")

    # Relative-position disjunction binaries (one set per unordered pair).
    left = {}
    right = {}
    below = {}
    above = {}
    for i in range(n):
        for j in range(i + 1, n):
            left[i, j] = model.addVar(vtype=GRB.BINARY, name="left_%d_%d" % (i, j))
            right[i, j] = model.addVar(vtype=GRB.BINARY, name="right_%d_%d" % (i, j))
            below[i, j] = model.addVar(vtype=GRB.BINARY, name="below_%d_%d" % (i, j))
            above[i, j] = model.addVar(vtype=GRB.BINARY, name="above_%d_%d" % (i, j))

    M = float(max(sheet_width, sheet_length))

    # Each billboard is assigned to exactly one sheet.
    for i in range(n):
        model.addConstr(gp.quicksum(a[i, k] for k in range(K)) == 1, name="assign_%d" % i)

    # Containment: billboard lies fully inside a sheet (all sheets identical).
    for i in range(n):
        model.addConstr(x[i] <= sheet_width - bw[i], name="contain_x_%d" % i)
        model.addConstr(y[i] <= sheet_length - bh[i], name="contain_y_%d" % i)

    # Link sheet-usage indicator to assignments.
    for k in range(K):
        for i in range(n):
            model.addConstr(z[k] >= a[i, k], name="use_%d_%d" % (k, i))

    # Non-overlap: when i and j share a sheet, one of the four separations must
    # hold (i left/right/below/above of j).
    for i in range(n):
        for j in range(i + 1, n):
            model.addConstr(x[i] + bw[i] <= x[j] + M * (1 - left[i, j]), name="sep_left_%d_%d" % (i, j))
            model.addConstr(x[j] + bw[j] <= x[i] + M * (1 - right[i, j]), name="sep_right_%d_%d" % (i, j))
            model.addConstr(y[i] + bh[i] <= y[j] + M * (1 - below[i, j]), name="sep_below_%d_%d" % (i, j))
            model.addConstr(y[j] + bh[j] <= y[i] + M * (1 - above[i, j]), name="sep_above_%d_%d" % (i, j))
            for k in range(K):
                model.addConstr(
                    left[i, j] + right[i, j] + below[i, j] + above[i, j] >= a[i, k] + a[j, k] - 1,
                    name="nooverlap_%d_%d_%d" % (i, j, k),
                )

    # Symmetry breaking: consume sheets in index order.
    for k in range(K - 1):
        model.addConstr(z[k] >= z[k + 1], name="sym_%d" % k)

    model.setObjective(gp.quicksum(z[k] for k in range(K)), GRB.MINIMIZE)
    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": "solver_status_%d" % model.status}