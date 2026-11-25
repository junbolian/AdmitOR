import gurobipy as gp
from gurobipy import GRB
from itertools import permutations

def solve(params):
    processing_times = params["processing_times"]

    jobs = list(range(len(processing_times)))
    machines = list(range(len(processing_times[0])))
    n_jobs = len(jobs)
    n_machines = len(machines)

    # Big-M for disjunctive constraints
    M = sum(processing_times[j][k] for j in jobs for k in machines) + 1

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Start times for each job on each machine
    start = {}
    for j in jobs:
        for k in machines:
            start[j, k] = model.addVar(lb=0.0, vtype=GRB.CONTINUOUS, name=f"start_{j}_{k}")

    # Makespan
    makespan = model.addVar(lb=0.0, vtype=GRB.CONTINUOUS, name="makespan")

    # Binary: order[j1, j2, k] = 1 if job j1 precedes job j2 on machine k
    order = {}
    for k in machines:
        for j1 in jobs:
            for j2 in jobs:
                if j1 != j2:
                    order[j1, j2, k] = model.addVar(vtype=GRB.BINARY, name=f"order_{j1}_{j2}_{k}")

    model.update()

    # 1. Technological order: each job must finish on machine k before starting on machine k+1
    for j in jobs:
        for k in machines[:-1]:
            model.addConstr(
                start[j, k + 1] >= start[j, k] + processing_times[j][k],
                name=f"tech_{j}_{k}"
            )

    # 2. Machine capacity: no two jobs overlap on the same machine (disjunctive)
    for k in machines:
        for j1 in jobs:
            for j2 in jobs:
                if j1 < j2:
                    # Either j1 before j2 or j2 before j1
                    model.addConstr(
                        order[j1, j2, k] + order[j2, j1, k] == 1,
                        name=f"order_sum_{j1}_{j2}_{k}"
                    )
                    model.addConstr(
                        start[j2, k] >= start[j1, k] + processing_times[j1][k] - M * (1 - order[j1, j2, k]),
                        name=f"seq_{j1}_{j2}_{k}"
                    )
                    model.addConstr(
                        start[j1, k] >= start[j2, k] + processing_times[j2][k] - M * (1 - order[j2, j1, k]),
                        name=f"seq_{j2}_{j1}_{k}"
                    )

    # 3. Makespan definition: completion of all jobs on last machine
    last_machine = machines[-1]
    for j in jobs:
        model.addConstr(
            makespan >= start[j, last_machine] + processing_times[j][last_machine],
            name=f"makespan_{j}"
        )

    model.setObjective(makespan, GRB.MINIMIZE)

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver_status_{model.Status}"}