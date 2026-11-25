import gurobipy as gp
from gurobipy import GRB

def solve(params):
    n_vars = 10
    # Upper bound on registers needed (worst case = n_vars)
    n_regs = n_vars

    # Interference pairs (hardcoded as structural constants per problem definition)
    interference = [
        (5, 8), (4, 9), (3, 7), (0, 3), (1, 4),
        (2, 3), (6, 7), (4, 5), (3, 9), (5, 9), (6, 9)
    ]

    model = gp.Model("register_allocation")
    model.setParam("OutputFlag", 0)

    # x[i, r] = 1 if variable i is assigned register r
    x = model.addVars(n_vars, n_regs, vtype=GRB.BINARY, name="x")

    # y[r] = 1 if register r is used by at least one variable
    y = model.addVars(n_regs, vtype=GRB.BINARY, name="y")

    # Objective: minimize number of distinct registers used
    model.setObjective(gp.quicksum(y[r] for r in range(n_regs)), GRB.MINIMIZE)

    # Each variable assigned exactly one register
    for i in range(n_vars):
        model.addConstr(gp.quicksum(x[i, r] for r in range(n_regs)) == 1,
                        name=f"assign_{i}")

    # Interfering variables cannot share a register
    for (i, j) in interference:
        for r in range(n_regs):
            model.addConstr(x[i, r] + x[j, r] <= 1,
                            name=f"interfere_{i}_{j}_{r}")

    # y[r] must be 1 if any variable uses register r
    for r in range(n_regs):
        for i in range(n_vars):
            model.addConstr(y[r] >= x[i, r], name=f"use_{r}_{i}")

    # Symmetry breaking: register r can only be used if r-1 is used
    for r in range(1, n_regs):
        model.addConstr(y[r] <= y[r - 1], name=f"sym_{r}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"solver_status_{model.Status}"}