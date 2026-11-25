import gurobipy as gp
from gurobipy import GRB

def solve(params):
    sheet_width = params["sheet_width"]
    sheet_height = params["sheet_height"]
    part_widths = params["part_widths"]   # list of 4
    part_heights = params["part_heights"] # list of 4

    n_parts = 4
    # Upper bound on sheets needed: each part on its own sheet
    n_sheets = n_parts

    parts = range(n_parts)
    sheets = range(n_sheets)

    model = gp.Model("steel_nesting")
    model.setParam("OutputFlag", 0)
    model.setParam("TimeLimit", 120)

    # a[i][k] = 1 if part i is assigned to sheet k
    a = {}
    for i in parts:
        for k in sheets:
            a[i, k] = model.addVar(vtype=GRB.BINARY, name=f"a_{i}_{k}")

    # y[k] = 1 if sheet k is used
    y = {}
    for k in sheets:
        y[k] = model.addVar(vtype=GRB.BINARY, name=f"y_{k}")

    # x, z: continuous position of bottom-left corner of each part
    x = {}
    z = {}
    for i in parts:
        x[i] = model.addVar(lb=0.0, ub=sheet_width, vtype=GRB.CONTINUOUS, name=f"x_{i}")
        z[i] = model.addVar(lb=0.0, ub=sheet_height, vtype=GRB.CONTINUOUS, name=f"z_{i}")

    # Each part assigned to exactly one sheet
    for i in parts:
        model.addConstr(gp.quicksum(a[i, k] for k in sheets) == 1, name=f"assign_{i}")

    # Sheet used if any part assigned to it
    for i in parts:
        for k in sheets:
            model.addConstr(y[k] >= a[i, k], name=f"sheet_use_{i}_{k}")

    # Parts must fit within sheet boundaries
    for i in parts:
        model.addConstr(x[i] + part_widths[i] <= sheet_width, name=f"fit_w_{i}")
        model.addConstr(z[i] + part_heights[i] <= sheet_height, name=f"fit_h_{i}")

    # Non-overlap constraints for each pair of parts on the same sheet
    # For parts i and j on the same sheet k:
    # at least one of: i left of j, i right of j, i below j, i above j
    # We use big-M with binary indicators and enforce when both parts are on same sheet

    M_w = sheet_width
    M_h = sheet_height

    # For each pair (i, j) with i < j, and each sheet k:
    # d[i,j,k,dir] = 1 if separation in direction dir
    # sum of d >= 1 when both i,j on sheet k (i.e., a[i,k]+a[j,k] >= 2 implies sum>=1)
    # Encoded as: sum_dir d[i,j,k,dir] >= a[i,k] + a[j,k] - 1

    for i in parts:
        for j in parts:
            if i >= j:
                continue
            for k in sheets:
                d = {}
                for direc in range(4):
                    d[direc] = model.addVar(vtype=GRB.BINARY, name=f"d_{i}_{j}_{k}_{direc}")

                # sum of directions >= a[i,k] + a[j,k] - 1
                model.addConstr(
                    gp.quicksum(d[direc] for direc in range(4)) >= a[i, k] + a[j, k] - 1,
                    name=f"sep_{i}_{j}_{k}"
                )

                # d[0]: i is left of j  => x[i] + pw[i] <= x[j] + M*(1-d[0])
                model.addConstr(
                    x[i] + part_widths[i] <= x[j] + M_w * (1 - d[0]),
                    name=f"left_{i}_{j}_{k}"
                )
                # d[1]: i is right of j => x[j] + pw[j] <= x[i] + M*(1-d[1])
                model.addConstr(
                    x[j] + part_widths[j] <= x[i] + M_w * (1 - d[1]),
                    name=f"right_{i}_{j}_{k}"
                )
                # d[2]: i is below j => z[i] + ph[i] <= z[j] + M*(1-d[2])
                model.addConstr(
                    z[i] + part_heights[i] <= z[j] + M_h * (1 - d[2]),
                    name=f"below_{i}_{j}_{k}"
                )
                # d[3]: i is above j => z[j] + ph[j] <= z[i] + M*(1-d[3])
                model.addConstr(
                    z[j] + part_heights[j] <= z[i] + M_h * (1 - d[3]),
                    name=f"above_{i}_{j}_{k}"
                )

    # Symmetry breaking: sheet k can only be used if sheet k-1 is used
    for k in range(1, n_sheets):
        model.addConstr(y[k] <= y[k - 1], name=f"sym_sheet_{k}")

    # Objective: minimize number of sheets used
    model.setObjective(gp.quicksum(y[k] for k in sheets), GRB.MINIMIZE)

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL or (status == GRB.TIME_LIMIT and model.SolCount > 0):
        obj = model.ObjVal
        sol_status = "optimal" if status == GRB.OPTIMAL else "time_limit_feasible"
        return {"objective": float(round(obj)), "status": sol_status}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"gurobi_status_{status}"}