import gurobipy as gp
from gurobipy import GRB

def solve(params):
    task_times = params["task_times"]  # 5x4 matrix, rows = workers I-V, cols = tasks A-D

    num_workers = len(task_times)      # 5
    num_tasks = len(task_times[0])     # 4

    workers = range(num_workers)
    tasks = range(num_tasks)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # x[i,j] = 1 if worker i is assigned to task j
    x = model.addVars(workers, tasks, vtype=GRB.BINARY, name="x")

    # Minimize total time
    model.setObjective(
        gp.quicksum(task_times[i][j] * x[i, j] for i in workers for j in tasks),
        GRB.MINIMIZE
    )

    # Each task must be assigned to exactly one worker
    for j in tasks:
        model.addConstr(gp.quicksum(x[i, j] for i in workers) == 1, name=f"task_{j}")

    # Each worker can be assigned to at most one task
    for i in workers:
        model.addConstr(gp.quicksum(x[i, j] for j in tasks) <= 1, name=f"worker_{i}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}