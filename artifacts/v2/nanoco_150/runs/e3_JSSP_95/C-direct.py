import gurobipy as gp
from gurobipy import GRB

def solve(params):
    processing_times = params["processing_times"]

    # Structural routes: ordered list of stations each batch must visit
    routes = [
        [2, 0, 1],  # J0: Station 2 -> Station 0 -> Station 1
        [0, 2, 1],  # J1: Station 0 -> Station 2 -> Station 1
        [0, 2, 1],  # J2: Station 0 -> Station 2 -> Station 1
    ]

    num_jobs = len(processing_times)
    num_ops = [len(processing_times[j]) for j in range(num_jobs)]

    model = gp.Model("pcb_scheduling")
    model.Params.OutputFlag = 0

    # Start-time variable for each operation of each job
    s = {}
    for j in range(num_jobs):
        for k in range(num_ops[j]):
            s[j, k] = model.addVar(lb=0, vtype=GRB.CONTINUOUS, name=f"s_{j}_{k}")

    # Makespan
    C = model.addVar(lb=0, vtype=GRB.CONTINUOUS, name="Cmax")

    # Big-M: upper bound on makespan
    M = sum(sum(processing_times[j]) for j in range(num_jobs))

    # Precedence within each job: operation k must finish before k+1 starts
    for j in range(num_jobs):
        for k in range(num_ops[j] - 1):
            model.addConstr(s[j, k + 1] >= s[j, k] + processing_times[j][k])

    # Group operations by station for disjunctive constraints
    station_ops = {}
    for j in range(num_jobs):
        for k in range(num_ops[j]):
            st = routes[j][k]
            station_ops.setdefault(st, []).append((j, k))

    # Disjunctive: no two operations on the same station can overlap
    for st, ops in station_ops.items():
        for a in range(len(ops)):
            for b in range(a + 1, len(ops)):
                j1, k1 = ops[a]
                j2, k2 = ops[b]
                p1 = processing_times[j1][k1]
                p2 = processing_times[j2][k2]

                y = model.addVar(vtype=GRB.BINARY, name=f"y_{j1}_{k1}_{j2}_{k2}")

                # y = 1  ->  (j1,k1) precedes (j2,k2)
                # y = 0  ->  (j2,k2) precedes (j1,k1)
                model.addConstr(s[j1, k1] + p1 <= s[j2, k2] + M * (1 - y))
                model.addConstr(s[j2, k2] + p2 <= s[j1, k1] + M * y)

    # Makespan >= completion time of every job's last operation
    for j in range(num_jobs):
        last = num_ops[j] - 1
        model.addConstr(C >= s[j, last] + processing_times[j][last])

    model.setObjective(C, GRB.MINIMIZE)
    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    else:
        return {"objective": None, "status": "failed"}