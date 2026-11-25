import gurobipy as gp
from gurobipy import GRB

def solve(params):
    duration = {
        ('J0', 'M0'): params["duration_J0_M0"],
        ('J0', 'M1'): params["duration_J0_M1"],
        ('J0', 'M2'): params["duration_J0_M2"],
        ('J1', 'M0'): params["duration_J1_M0"],
        ('J1', 'M1'): params["duration_J1_M1"],
        ('J1', 'M2'): params["duration_J1_M2"],
        ('J2', 'M0'): params["duration_J2_M0"],
        ('J2', 'M1'): params["duration_J2_M1"],
        ('J2', 'M2'): params["duration_J2_M2"],
    }

    jobs = ['J0', 'J1', 'J2']
    machines = ['M0', 'M1', 'M2']

    # Big-M: upper bound on makespan
    big_M = sum(duration[j, m] for j in jobs for m in machines)

    model = gp.Model("flexible_job_shop")
    model.setParam("OutputFlag", 0)

    # Start time of job j on machine m
    start = {
        (j, m): model.addVar(lb=0.0, name=f"start_{j}_{m}")
        for j in jobs for m in machines
    }

    # Makespan
    makespan = model.addVar(lb=0.0, name="makespan")

    # Binary: z[j1,j2,m] = 1 if job j1 precedes job j2 on machine m
    z = {
        (j1, j2, m): model.addVar(vtype=GRB.BINARY, name=f"z_{j1}_{j2}_{m}")
        for j1 in jobs for j2 in jobs if j1 != j2
        for m in machines
    }

    model.setObjective(makespan, GRB.MINIMIZE)

    # Makespan must be at least the completion time of every task
    for j in jobs:
        for m in machines:
            model.addConstr(makespan >= start[j, m] + duration[j, m],
                            name=f"mkspan_{j}_{m}")

    # No overlap on each machine: for each pair of jobs on the same machine,
    # one must finish before the other starts.
    for m in machines:
        for j1 in jobs:
            for j2 in jobs:
                if j1 >= j2:
                    continue
                # j1 before j2
                model.addConstr(
                    start[j1, m] + duration[j1, m] <= start[j2, m] + big_M * (1 - z[j1, j2, m]),
                    name=f"seq_{j1}_{j2}_{m}_a"
                )
                # j2 before j1
                model.addConstr(
                    start[j2, m] + duration[j2, m] <= start[j1, m] + big_M * z[j1, j2, m],
                    name=f"seq_{j1}_{j2}_{m}_b"
                )

    # No overlap per job: each job can be on only one machine at a time.
    # For each job and each pair of machines, one task must finish before the other starts.
    w = {
        (j, m1, m2): model.addVar(vtype=GRB.BINARY, name=f"w_{j}_{m1}_{m2}")
        for j in jobs
        for m1 in machines for m2 in machines if m1 < m2
    }

    for j in jobs:
        for m1 in machines:
            for m2 in machines:
                if m1 >= m2:
                    continue
                # m1 before m2
                model.addConstr(
                    start[j, m1] + duration[j, m1] <= start[j, m2] + big_M * (1 - w[j, m1, m2]),
                    name=f"job_seq_{j}_{m1}_{m2}_a"
                )
                # m2 before m1
                model.addConstr(
                    start[j, m2] + duration[j, m2] <= start[j, m1] + big_M * w[j, m1, m2],
                    name=f"job_seq_{j}_{m1}_{m2}_b"
                )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.TIME_LIMIT:
        return {"objective": None, "status": "time_limit"}
    else:
        return {"objective": None, "status": f"gurobi_status_{model.Status}"}