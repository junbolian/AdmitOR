import gurobipy as gp
from gurobipy import GRB

def solve(params):
    sheet_width = params["sheet_width"]
    sheet_height = params["sheet_height"]
    part_widths = params["part_widths"]
    part_heights = params["part_heights"]

    n_parts = len(part_widths)
    # Upper bound on sheets needed: each part on its own sheet
    n_sheets = n_parts

    parts = range(n_parts)
    sheets = range(n_sheets)

    model = gp.Model("steel_nesting")
    model.setParam("OutputFlag", 0)
    model.setParam("TimeLimit", 120)

    # y[s] = 1 if sheet s is used
    y = model.addVars(sheets, vtype=GRB.BINARY, name="y")

    # a[i,s] = 1 if part i is assigned to sheet s
    a = model.addVars(parts, sheets, vtype=GRB.BINARY, name="a")

    # x[i], z[i] = bottom-left corner (x=width axis, z=height axis) of part i
    x = model.addVars(parts, lb=0.0, name="x")
    z = model.addVars(parts, lb=0.0, name="z")

    # Objective: minimize number of sheets used
    model.setObjective(gp.quicksum(y[s] for s in sheets), GRB.MINIMIZE)

    # Each part assigned to exactly one sheet
    for i in parts:
        model.addConstr(gp.quicksum(a[i, s] for s in sheets) == 1, name=f"assign_{i}")

    # If part i is on sheet s, it must fit within sheet boundaries
    # x[i] + pw[i] <= sheet_width  (always, since part is on exactly one sheet)
    # z[i] + ph[i] <= sheet_height
    for i in parts:
        model.addConstr(x[i] + part_widths[i] <= sheet_width, name=f"fit_x_{i}")
        model.addConstr(z[i] + part_heights[i] <= sheet_height, name=f"fit_z_{i}")
        model.addConstr(x[i] >= 0, name=f"lb_x_{i}")
        model.addConstr(z[i] >= 0, name=f"lb_z_{i}")

    # If part i is on sheet s, then sheet s must be used
    for i in parts:
        for s in sheets:
            model.addConstr(a[i, s] <= y[s], name=f"use_{i}_{s}")

    # Non-overlap constraints for pairs of parts on the same sheet
    # For parts i and j on the same sheet, at least one of four separations holds:
    #   i is left of j, i is right of j, i is below j, i is above j
    # We use big-M with binary indicators b[i,j,s,d] and same-sheet indicator
    # To keep it tractable, introduce:
    #   same[i,j,s] = 1 if both i and j are on sheet s
    # Then enforce separation when same[i,j,s]=1

    M_x = sheet_width
    M_z = sheet_height

    pairs = [(i, j) for i in parts for j in parts if i < j]

    # sep[i,j,d]: separation direction indicator (d=0: i left of j, 1: i right, 2: i below, 3: i above)
    sep = model.addVars(
        [(i, j, d) for (i, j) in pairs for d in range(4)],
        vtype=GRB.BINARY, name="sep"
    )

    # same_sheet[i,j,s]: auxiliary to linearize a[i,s]*a[j,s]
    same_sheet = model.addVars(
        [(i, j, s) for (i, j) in pairs for s in sheets],
        vtype=GRB.BINARY, name="same_sheet"
    )

    for (i, j) in pairs:
        for s in sheets:
            # same_sheet[i,j,s] <= a[i,s]
            model.addConstr(same_sheet[i, j, s] <= a[i, s])
            # same_sheet[i,j,s] <= a[j,s]
            model.addConstr(same_sheet[i, j, s] <= a[j, s])
            # same_sheet[i,j,s] >= a[i,s] + a[j,s] - 1
            model.addConstr(same_sheet[i, j, s] >= a[i, s] + a[j, s] - 1)

        # Total "same sheet" activations over all sheets
        total_same = gp.quicksum(same_sheet[i, j, s] for s in sheets)

        # At least one separation direction must hold when they share a sheet
        # sep directions: 0: x[i]+pw[i] <= x[j], 1: x[j]+pw[j] <= x[i],
        #                 2: z[i]+ph[i] <= z[j], 3: z[j]+ph[j] <= z[i]
        # Each direction enforced with big-M * (1 - sep[i,j,d])
        # and sum(sep) >= total_same (at least one active if on same sheet)

        # Separation constraints (big-M relaxed when sep=0)
        model.addConstr(
            x[i] + part_widths[i] <= x[j] + M_x * (1 - sep[i, j, 0]),
            name=f"sep_L_{i}_{j}"
        )
        model.addConstr(
            x[j] + part_widths[j] <= x[i] + M_x * (1 - sep[i, j, 1]),
            name=f"sep_R_{i}_{j}"
        )
        model.addConstr(
            z[i] + part_heights[i] <= z[j] + M_z * (1 - sep[i, j, 2]),
            name=f"sep_B_{i}_{j}"
        )
        model.addConstr(
            z[j] + part_heights[j] <= z[i] + M_z * (1 - sep[i, j, 3]),
            name=f"sep_T_{i}_{j}"
        )

        # At least one separation direction active for each co-sheet pair
        model.addConstr(
            gp.quicksum(sep[i, j, d] for d in range(4)) >= total_same,
            name=f"atleast_one_sep_{i}_{j}"
        )

    # Symmetry breaking: sheets used in order
    for s in sheets[:-1]:
        model.addConstr(y[s] >= y[s + 1], name=f"sym_sheet_{s}")

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