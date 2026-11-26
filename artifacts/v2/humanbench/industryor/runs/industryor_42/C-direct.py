import gurobipy as gp
from gurobipy import GRB


def solve(params):
    cpu_freqs = params["cpu_frequencies_ghz"]
    task_instr = params["task_instructions_bi"]
    num_tasks = int(params["num_tasks"])
    num_cpus = int(params["num_cpus"])

    tasks = range(num_tasks)
    cpus = range(num_cpus)

    model = gp.Model("cpu_scheduling")
    model.Params.OutputFlag = 0

    bigM = 1e6

    # Assignment: x[i, j] = 1 if task i runs on cpu j
    x = model.addVars(tasks, cpus, vtype=GRB.BINARY, name="x")
    # Start time of task i on cpu j
    start = model.addVars(tasks, cpus, vtype=GRB.CONTINUOUS, lb=0.0, name="start")
    # Completion time of task i
    comp = model.addVars(tasks, vtype=GRB.CONTINUOUS, lb=0.0, name="comp")
    makespan = model.addVar(vtype=GRB.CONTINUOUS, lb=0.0, name="makespan")

    # Execution time of task i on cpu j
    proc = {
        (i, j): task_instr[i] / cpu_freqs[j] if cpu_freqs[j] > 0 else bigM
        for i in tasks
        for j in cpus
    }

    # Each task assigned to exactly one cpu
    model.addConstrs(
        (gp.quicksum(x[i, j] for j in cpus) == 1 for i in tasks), name="assign"
    )

    # Task can only start on a cpu it is assigned to
    model.addConstrs(
        (start[i, j] <= bigM * x[i, j] for i in tasks for j in cpus),
        name="link",
    )

    # Completion time bounds (active only when assigned)
    for i in tasks:
        for j in cpus:
            model.addConstr(
                comp[i] >= start[i, j] + proc[i, j] - bigM * (1 - x[i, j]),
                name=f"comp_{i}_{j}",
            )

    # No two tasks on the same cpu overlap (disjunctive)
    for j in cpus:
        for i in tasks:
            for k in tasks:
                if i < k:
                    y = model.addVar(vtype=GRB.BINARY, name=f"order_{i}_{k}_{j}")
                    model.addConstr(
                        start[k, j] >= start[i, j] + proc[i, j] - bigM * (1 - y) - bigM * (2 - x[i, j] - x[k, j]),
                        name=f"seq_a_{i}_{k}_{j}",
                    )
                    model.addConstr(
                        start[i, j] >= start[k, j] + proc[k, j] - bigM * y - bigM * (2 - x[i, j] - x[k, j]),
                        name=f"seq_b_{i}_{k}_{j}",
                    )

    # Makespan
    model.addConstrs((makespan >= comp[i] for i in tasks), name="ms")

    model.setObjective(makespan, GRB.MINIMIZE)

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    if model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    return {"objective": None, "status": "no_solution"}