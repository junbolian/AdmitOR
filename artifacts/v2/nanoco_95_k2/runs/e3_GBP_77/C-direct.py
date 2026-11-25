import gurobipy as gp
from gurobipy import GRB

def solve(params):
    sheet_width = params["sheet_width"]
    sheet_height = params["sheet_height"]
    part_widths = params["part_widths"]
    part_heights = params["part_heights"]

    n_parts = len(part_widths)
    # Upper bound on sheets needed: each part on its own sheet
    max_sheets = n_parts

    model = gp.Model("steel_nesting")
    model.setParam("OutputFlag", 0)

    # Binary: part i assigned to sheet k
    assign = model.addVars(n_parts, max_sheets, vtype=GRB.BINARY, name="assign")

    # Binary: sheet k is used
    used = model.addVars(max_sheets, vtype=GRB.BINARY, name="used")

    # Continuous: x, y position of bottom-left corner of part i on its sheet
    x = model.addVars(n_parts, max_sheets, lb=0.0, name="x")
    y = model.addVars(n_parts, max_sheets, lb=0.0, name="y")

    # Non-overlap auxiliary binaries: for each pair (i,j) on sheet k, one of four separating conditions
    # b[i,j,k,d]: part i is to the left (d=0), right (d=1), below (d=2), above (d=3) part j on sheet k
    pairs = [(i, j) for i in range(n_parts) for j in range(i+1, n_parts)]
    b = model.addVars(
        [(i, j, k, d) for (i, j) in pairs for k in range(max_sheets) for d in range(4)],
        vtype=GRB.BINARY, name="b"
    )

    # Big-M values based on sheet dimensions
    M_x = sheet_width
    M_y = sheet_height

    # Objective: minimize number of sheets used
    model.setObjective(gp.quicksum(used[k] for k in range(max_sheets)), GRB.MINIMIZE)

    # Each part assigned to exactly one sheet
    for i in range(n_parts):
        model.addConstr(gp.quicksum(assign[i, k] for k in range(max_sheets)) == 1,
                        name=f"assign_part_{i}")

    # Sheet used if any part assigned to it
    for k in range(max_sheets):
        for i in range(n_parts):
            model.addConstr(used[k] >= assign[i, k], name=f"used_{k}_{i}")

    # Symmetry breaking: sheets used in order
    for k in range(max_sheets - 1):
        model.addConstr(used[k] >= used[k + 1], name=f"sym_break_{k}")

    # Boundary constraints: part i fits within sheet k if assigned
    for i in range(n_parts):
        for k in range(max_sheets):
            # x[i,k] + part_widths[i] <= sheet_width + M*(1 - assign[i,k])
            model.addConstr(
                x[i, k] + part_widths[i] <= sheet_width + M_x * (1 - assign[i, k]),
                name=f"bnd_x_{i}_{k}"
            )
            model.addConstr(
                y[i, k] + part_heights[i] <= sheet_height + M_y * (1 - assign[i, k]),
                name=f"bnd_y_{i}_{k}"
            )
            # Position only meaningful when assigned; force to 0 otherwise (optional, helps solver)
            model.addConstr(x[i, k] <= M_x * assign[i, k], name=f"xub_{i}_{k}")
            model.addConstr(y[i, k] <= M_y * assign[i, k], name=f"yub_{i}_{k}")

    # Non-overlap constraints for each pair on the same sheet
    for (i, j) in pairs:
        for k in range(max_sheets):
            # At least one separating condition must hold when both parts are on sheet k
            # both_on_k <= assign[i,k] + assign[j,k] - 1
            # Sum of b >= both_on_k enforced via:
            # b[i,j,k,0] + b[i,j,k,1] + b[i,j,k,2] + b[i,j,k,3] >= assign[i,k] + assign[j,k] - 1
            model.addConstr(
                gp.quicksum(b[i, j, k, d] for d in range(4)) >= assign[i, k] + assign[j, k] - 1,
                name=f"sep_sum_{i}_{j}_{k}"
            )

            # d=0: i is left of j: x[i,k] + part_widths[i] <= x[j,k] + M*(1 - b[i,j,k,0])
            model.addConstr(
                x[i, k] + part_widths[i] <= x[j, k] + M_x * (1 - b[i, j, k, 0]),
                name=f"sep_left_{i}_{j}_{k}"
            )
            # d=1: i is right of j: x[j,k] + part_widths[j] <= x[i,k] + M*(1 - b[i,j,k,1])
            model.addConstr(
                x[j, k] + part_widths[j] <= x[i, k] + M_x * (1 - b[i, j, k, 1]),
                name=f"sep_right_{i}_{j}_{k}"
            )
            # d=2: i is below j: y[i,k] + part_heights[i] <= y[j,k] + M*(1 - b[i,j,k,2])
            model.addConstr(
                y[i, k] + part_heights[i] <= y[j, k] + M_y * (1 - b[i, j, k, 2]),
                name=f"sep_below_{i}_{j}_{k}"
            )
            # d=3: i is above j: y[j,k] + part_heights[j] <= y[i,k] + M*(1 - b[i,j,k,3])
            model.addConstr(
                y[j, k] + part_heights[j] <= y[i, k] + M_y * (1 - b[i, j, k, 3]),
                name=f"sep_above_{i}_{j}_{k}"
            )

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver_status_{status}"}