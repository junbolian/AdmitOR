import gurobipy as gp
from gurobipy import GRB

def solve(params):
    processing_time = params["processing_time"]

    n = 4  # number of batches
    m = 3   # number of units

    # p[i][j] = processing time of batch i at unit j (0-indexed)
    p = {}
    for i in range(n):
        for j in range(m):
            p[i, j] = float(processing_time[i][j])

    model = gp.Model("flowshop")
    model.setParam("OutputFlag", 0)

    # Binary: x[i][k] = 1 if batch i is assigned to position k
    x = model.addVars(range(n), range(n), vtype=GRB.BINARY, name="x")

    # Start time of the batch in position k at unit j
    S = model.addVars(range(n), range(m), lb=0.0, name="S")

    # Makespan
    Cmax = model.addVar(lb=0.0, name="Cmax")

    # Each batch assigned to exactly one position
    for i in range(n):
        model.addConstr(gp.quicksum(x[i, k] for k in range(n)) == 1, name=f"assign_batch_{i}")

    # Each position gets exactly one batch
    for k in range(n):
        model.addConstr(gp.quicksum(x[i, k] for i in range(n)) == 1, name=f"assign_pos_{k}")

    # Processing time of batch in position k at unit j
    pt = {}
    for k in range(n):
        for j in range(m):
            pt[k, j] = model.addVar(lb=0.0, name=f"pt_{k}_{j}")
            model.addConstr(
                pt[k, j] == gp.quicksum(x[i, k] * p[i, j] for i in range(n)),
                name=f"def_pt_{k}_{j}"
            )

    # First position, first unit starts at 0
    model.addConstr(S[0, 0] == 0, name="start_first")

    # Unit sequence for position 0: each unit starts after previous finishes
    for j in range(1, m):
        model.addConstr(S[0, j] >= S[0, j-1] + pt[0, j-1], name=f"unit_seq_pos0_{j}")

    # Position sequence for unit 0: next position starts after current finishes
    for k in range(1, n):
        model.addConstr(S[k, 0] >= S[k-1, 0] + pt[k-1, 0], name=f"pos_seq_U0_{k}")

    # General constraints: for position k (k>0) and unit j (j>0)
    for k in range(1, n):
        for j in range(1, m):
            model.addConstr(
                S[k, j] >= S[k-1, j] + pt[k-1, j],
                name=f"pos_seq_{k}_{j}"
            )
            model.addConstr(
                S[k, j] >= S[k, j-1] + pt[k, j-1],
                name=f"unit_seq_{k}_{j}"
            )

    # Makespan = completion of last position at last unit
    model.addConstr(Cmax >= S[n-1, m-1] + pt[n-1, m-1], name="makespan")

    model.setObjective(Cmax, GRB.MINIMIZE)
    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.TIME_LIMIT:
        return {"objective": None, "status": "time_limit"}
    else:
        return {"objective": None, "status": f"solver_status_{model.Status}"}