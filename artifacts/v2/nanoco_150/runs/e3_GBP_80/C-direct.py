import gurobipy as gp
from gurobipy import GRB

def solve(params):
    wafer_width = params["wafer_width"]
    wafer_height = params["wafer_height"]
    ic_widths = [
        params["ic1_width"], params["ic2_width"], params["ic3_width"],
        params["ic4_width"], params["ic5_width"]
    ]
    ic_heights = [
        params["ic1_height"], params["ic2_height"], params["ic3_height"],
        params["ic4_height"], params["ic5_height"]
    ]

    n_ics = 5
    ics = list(range(n_ics))

    for i in ics:
        if ic_widths[i] > wafer_width or ic_heights[i] > wafer_height:
            return {"objective": None, "status": "infeasible"}

    max_wafers = n_ics
    wafers = list(range(max_wafers))
    M = 2 * max(wafer_width, wafer_height)

    model = gp.Model("wafer_packing")
    model.Params.OutputFlag = 0

    x = {}
    for i in ics:
        for k in wafers:
            x[i, k] = model.addVar(vtype=GRB.BINARY, name=f"x_{i}_{k}")

    y = {}
    for k in wafers:
        y[k] = model.addVar(vtype=GRB.BINARY, name=f"y_{k}")

    px = {}
    py = {}
    for i in ics:
        px[i] = model.addVar(lb=0, ub=wafer_width - ic_widths[i], name=f"px_{i}")
        py[i] = model.addVar(lb=0, ub=wafer_height - ic_heights[i], name=f"py_{i}")

    z_ijk = {}
    for i in ics:
        for j in ics:
            if i < j:
                for k in wafers:
                    z_ijk[i, j, k] = model.addVar(vtype=GRB.BINARY, name=f"z_{i}_{j}_{k}")

    z_same = {}
    for i in ics:
        for j in ics:
            if i < j:
                z_same[i, j] = model.addVar(vtype=GRB.BINARY, name=f"zs_{i}_{j}")

    L = {}
    R = {}
    A = {}
    B = {}
    for i in ics:
        for j in ics:
            if i < j:
                L[i, j] = model.addVar(vtype=GRB.BINARY, name=f"L_{i}_{j}")
                R[i, j] = model.addVar(vtype=GRB.BINARY, name=f"R_{i}_{j}")
                A[i, j] = model.addVar(vtype=GRB.BINARY, name=f"A_{i}_{j}")
                B[i, j] = model.addVar(vtype=GRB.BINARY, name=f"B_{i}_{j}")

    model.update()

    for i in ics:
        model.addConstr(gp.quicksum(x[i, k] for k in wafers) == 1, name=f"assign_{i}")

    for k in wafers:
        for i in ics:
            model.addConstr(x[i, k] <= y[k], name=f"use_{i}_{k}")

    for k in range(1, len(wafers)):
        model.addConstr(y[k] <= y[k - 1], name=f"sym_{k}")

    for i in ics:
        for j in ics:
            if i < j:
                for k in wafers:
                    model.addConstr(z_ijk[i, j, k] <= x[i, k], name=f"zl1_{i}_{j}_{k}")
                    model.addConstr(z_ijk[i, j, k] <= x[j, k], name=f"zl2_{i}_{j}_{k}")
                    model.addConstr(z_ijk[i, j, k] >= x[i, k] + x[j, k] - 1, name=f"zge_{i}_{j}_{k}")

    for i in ics:
        for j in ics:
            if i < j:
                model.addConstr(
                    z_same[i, j] == gp.quicksum(z_ijk[i, j, k] for k in wafers),
                    name=f"zs_{i}_{j}"
                )

    for i in ics:
        for j in ics:
            if i < j:
                model.addConstr(
                    L[i, j] + R[i, j] + A[i, j] + B[i, j] >= z_same[i, j],
                    name=f"no_{i}_{j}"
                )

    for i in ics:
        for j in ics:
            if i < j:
                model.addConstr(
                    px[i] + ic_widths[i] <= px[j] + M * (1 - L[i, j]) + M * (1 - z_same[i, j]),
                    name=f"left_{i}_{j}"
                )
                model.addConstr(
                    px[j] + ic_widths[j] <= px[i] + M * (1 - R[i, j]) + M * (1 - z_same[i, j]),
                    name=f"right_{i}_{j}"
                )
                model.addConstr(
                    py[i] + ic_heights[i] <= py[j] + M * (1 - A[i, j]) + M * (1 - z_same[i, j]),
                    name=f"below_{i}_{j}"
                )
                model.addConstr(
                    py[j] + ic_heights[j] <= py[i] + M * (1 - B[i, j]) + M * (1 - z_same[i, j]),
                    name=f"above_{i}_{j}"
                )

    model.setObjective(gp.quicksum(y[k] for k in wafers), GRB.MINIMIZE)

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"status_{model.status}"}