import gurobipy as gp
from gurobipy import GRB


def solve(params):
    skill_scores = params["skill_scores"]
    max_load = params["max_skill_load_per_shift"]

    n = len(skill_scores)
    # Upper bound on shifts needed (worst case: one per staff member)
    max_shifts = n

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # x[i][j] = 1 if staff member i is assigned to shift j
    x = model.addVars(n, max_shifts, vtype=GRB.BINARY, name="x")
    # y[j] = 1 if shift j is opened
    y = model.addVars(max_shifts, vtype=GRB.BINARY, name="y")

    # Minimize number of open shifts
    model.setObjective(gp.quicksum(y[j] for j in range(max_shifts)), GRB.MINIMIZE)

    # Each staff member assigned to exactly one shift
    for i in range(n):
        model.addConstr(gp.quicksum(x[i, j] for j in range(max_shifts)) == 1, name=f"assign_{i}")

    # Skill load per shift must not exceed max_load
    for j in range(max_shifts):
        model.addConstr(
            gp.quicksum(skill_scores[i] * x[i, j] for i in range(n)) <= max_load * y[j],
            name=f"load_{j}"
        )

    # Symmetry breaking: shift j can only be used if shift j-1 is used
    for j in range(1, max_shifts):
        model.addConstr(y[j] <= y[j - 1], name=f"sym_{j}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}