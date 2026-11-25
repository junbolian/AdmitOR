import gurobipy as gp
from gurobipy import GRB

def solve(params):
    skill_scores = params["skill_scores"]
    shift_capacity = params["shift_capacity"]

    n = len(skill_scores)
    # Upper bound on shifts needed: at most n shifts (one per person)
    max_shifts = n

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # x[i][j] = 1 if staff member i is assigned to shift j
    x = [[model.addVar(vtype=GRB.BINARY, name=f"x_{i}_{j}")
          for j in range(max_shifts)]
         for i in range(n)]

    # y[j] = 1 if shift j is opened
    y = [model.addVar(vtype=GRB.BINARY, name=f"y_{j}")
         for j in range(max_shifts)]

    # Objective: minimize number of open shifts
    model.setObjective(gp.quicksum(y[j] for j in range(max_shifts)), GRB.MINIMIZE)

    # Each staff member assigned to exactly one shift
    for i in range(n):
        model.addConstr(
            gp.quicksum(x[i][j] for j in range(max_shifts)) == 1,
            name=f"assign_{i}"
        )

    # Capacity constraint per shift
    for j in range(max_shifts):
        model.addConstr(
            gp.quicksum(skill_scores[i] * x[i][j] for i in range(n)) <= shift_capacity * y[j],
            name=f"capacity_{j}"
        )

    # Symmetry breaking: shift j can only open if shift j-1 is open
    for j in range(1, max_shifts):
        model.addConstr(y[j] <= y[j - 1], name=f"symmetry_{j}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.TIME_LIMIT:
        return {"objective": None, "status": "time_limit"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}