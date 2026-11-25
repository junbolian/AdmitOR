import gurobipy as gp
from gurobipy import GRB

def solve(params):
    processing_time = params["processing_time"]
    big_M = params["big_M"]

    # Jobs: 0, 1, 2; Operations: 0, 1
    # Machine assignment (from problem structure):
    # Job 0 Op 0 -> Machine 0
    # Job 0 Op 1 -> Machine 1
    # Job 1 Op 0 -> Machine 0
    # Job 1 Op 1 -> Machine 2
    # Job 2 Op 0 -> Machine 1
    # Job 2 Op 1 -> Machine 2
    # (Classic 3-job 3-machine job shop routing)

    machine_assignment = {
        (0, 0): 0,
        (0, 1): 1,
        (1, 0): 0,
        (1, 1): 2,
        (2, 0): 1,
        (2, 1): 2,
    }

    model = gp.Model("jobshop")
    model.setParam("OutputFlag", 0)

    # Start time variables for each (job, operation)
    start = {}
    for j in range(3):
        for o in range(2):
            start[j, o] = model.addVar(lb=0.0, name=f"start_{j}_{o}")

    # Makespan variable
    makespan = model.addVar(lb=0.0, name="makespan")

    model.setObjective(makespan, GRB.MINIMIZE)

    # 1. Precedence constraints: op 1 starts after op 0 completes
    for j in range(3):
        model.addConstr(
            start[j, 1] >= start[j, 0] + processing_time,
            name=f"prec_{j}"
        )

    # 2. Machine capacity constraints
    # Collect all (job, op) pairs grouped by machine
    from collections import defaultdict
    machine_ops = defaultdict(list)
    for (j, o), mach in machine_assignment.items():
        machine_ops[mach].append((j, o))

    # For each machine, for each pair of operations, add disjunctive constraints
    order_vars = {}
    for mach, ops in machine_ops.items():
        for idx_a in range(len(ops)):
            for idx_b in range(idx_a + 1, len(ops)):
                ja, oa = ops[idx_a]
                jb, ob = ops[idx_b]
                # Binary: y=1 means (ja,oa) before (jb,ob); y=0 means (jb,ob) before (ja,oa)
                y = model.addVar(vtype=GRB.BINARY, name=f"order_{ja}_{oa}_{jb}_{ob}")
                order_vars[ja, oa, jb, ob] = y

                # If y=1: start[jb,ob] >= start[ja,oa] + processing_time
                model.addConstr(
                    start[jb, ob] >= start[ja, oa] + processing_time - big_M * (1 - y),
                    name=f"mach_{mach}_{ja}{oa}_{jb}{ob}_fwd"
                )
                # If y=0: start[ja,oa] >= start[jb,ob] + processing_time
                model.addConstr(
                    start[ja, oa] >= start[jb, ob] + processing_time - big_M * y,
                    name=f"mach_{mach}_{ja}{oa}_{jb}{ob}_bwd"
                )

    # 3. Makespan >= completion time of every operation
    for j in range(3):
        for o in range(2):
            model.addConstr(
                makespan >= start[j, o] + processing_time,
                name=f"mkspan_{j}_{o}"
            )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}