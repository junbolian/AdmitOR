import gurobipy as gp
from gurobipy import GRB

def solve(params):
    num_variables = params["num_variables"]
    interference_pairs = params["interference_pairs"]

    # Upper bound on registers needed: at most num_variables registers
    max_registers = num_variables

    model = gp.Model("register_allocation")
    model.setParam("OutputFlag", 0)

    # x[i][r] = 1 if variable i is assigned register r
    x = model.addVars(num_variables, max_registers, vtype=GRB.BINARY, name="x")

    # y[r] = 1 if register r is used by at least one variable
    y = model.addVars(max_registers, vtype=GRB.BINARY, name="y")

    # Objective: minimize number of distinct registers used
    model.setObjective(gp.quicksum(y[r] for r in range(max_registers)), GRB.MINIMIZE)

    # Each variable must be assigned exactly one register
    for i in range(num_variables):
        model.addConstr(
            gp.quicksum(x[i, r] for r in range(max_registers)) == 1,
            name=f"assign_{i}"
        )

    # Interfering variables must be assigned different registers
    for (i, j) in interference_pairs:
        for r in range(max_registers):
            model.addConstr(
                x[i, r] + x[j, r] <= 1,
                name=f"interfere_{i}_{j}_{r}"
            )

    # y[r] must be 1 if any variable uses register r
    for r in range(max_registers):
        for i in range(num_variables):
            model.addConstr(
                y[r] >= x[i, r],
                name=f"use_{r}_{i}"
            )

    # Symmetry breaking: register r can only be used if register r-1 is used
    for r in range(1, max_registers):
        model.addConstr(y[r] <= y[r - 1], name=f"sym_{r}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.TIME_LIMIT:
        return {"objective": None, "status": "time_limit"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}