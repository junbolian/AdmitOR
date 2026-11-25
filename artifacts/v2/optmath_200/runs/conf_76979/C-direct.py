import gurobipy as gp
from gurobipy import GRB

def solve(params):
    processing_time = params["processing_time_per_operation"]
    big_M = params["big_M"]

    # Problem structure: 3 jobs, 2 operations each
    # Machine assignments (standard job-shop example):
    # Job 0: Op 0 -> Machine 0, Op 1 -> Machine 1
    # Job 1: Op 0 -> Machine 1, Op 1 -> Machine 0
    # Job 2: Op 0 -> Machine 0, Op 1 -> Machine 1
    machine = {
        (0, 0): 0, (0, 1): 1,
        (1, 0): 1, (1, 1): 0,
        (2, 0): 0, (2, 1): 1,
    }

    jobs = [0, 1, 2]
    ops = [0, 1]

    model = gp.Model("job_shop")
    model.setParam("OutputFlag", 0)

    # Start time variables
    start = {}
    for j in jobs:
        for o in ops:
            start[j, o] = model.addVar(lb=0.0, name=f"start_{j}_{o}")

    # Makespan variable
    makespan = model.addVar(lb=0.0, name="makespan")

    # Binary sequencing variables for pairs of operations on the same machine
    # Collect all pairs (j1,o1) vs (j2,o2) on same machine where (j1,o1) < (j2,o2)
    same_machine_pairs = []
    op_list = [(j, o) for j in jobs for o in ops]
    for idx in range(len(op_list)):
        for jdx in range(idx + 1, len(op_list)):
            j1, o1 = op_list[idx]
            j2, o2 = op_list[jdx]
            if machine[j1, o1] == machine[j2, o2]:
                same_machine_pairs.append((j1, o1, j2, o2))

    seq = {}
    for (j1, o1, j2, o2) in same_machine_pairs:
        seq[j1, o1, j2, o2] = model.addVar(vtype=GRB.BINARY, name=f"seq_{j1}_{o1}_{j2}_{o2}")

    model.update()

    # Objective: minimize makespan
    model.setObjective(makespan, GRB.MINIMIZE)

    # Job precedence constraints: op 1 starts after op 0 finishes
    for j in jobs:
        model.addConstr(start[j, 1] >= start[j, 0] + processing_time, name=f"prec_{j}")

    # Makespan constraints: makespan >= completion of every operation
    for j in jobs:
        for o in ops:
            model.addConstr(makespan >= start[j, o] + processing_time, name=f"mksp_{j}_{o}")

    # Machine sequencing constraints
    for (j1, o1, j2, o2) in same_machine_pairs:
        s = seq[j1, o1, j2, o2]
        # If s = 1: (j1,o1) before (j2,o2)
        model.addConstr(
            start[j2, o2] >= start[j1, o1] + processing_time - big_M * (1 - s),
            name=f"mach_a_{j1}_{o1}_{j2}_{o2}"
        )
        # If s = 0: (j2,o2) before (j1,o1)
        model.addConstr(
            start[j1, o1] >= start[j2, o2] + processing_time - big_M * s,
            name=f"mach_b_{j1}_{o1}_{j2}_{o2}"
        )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver_status_{model.Status}"}