import gurobipy as gp
from gurobipy import GRB
from itertools import permutations

def solve(params):
    p = params["p"]  # p[j][m]: processing time of job j at machine m

    n_jobs = len(p)
    n_machines = len(p[0])
    jobs = list(range(n_jobs))
    machines = list(range(n_machines))

    # This is a permutation flowshop makespan minimization problem.
    # With n=4 jobs, we can enumerate all 4! = 24 permutations and pick the best,
    # but we'll use a MIP formulation as required.

    # Decision variables:
    # x[i,j] = 1 if job i is processed before job j in the sequence
    # C[j,m] = completion time of job j on machine m
    # Makespan = max completion time on last machine

    BIG_M = sum(p[j][m] for j in jobs for m in machines) + 1

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Completion time variables
    C = {}
    for j in jobs:
        for m in machines:
            C[j, m] = model.addVar(lb=0.0, name=f"C_{j}_{m}")

    # Ordering variables: x[i,j] = 1 if i precedes j
    x = {}
    for i in jobs:
        for j in jobs:
            if i != j:
                x[i, j] = model.addVar(vtype=GRB.BINARY, name=f"x_{i}_{j}")

    # Makespan variable
    makespan = model.addVar(lb=0.0, name="makespan")

    model.setObjective(makespan, GRB.MINIMIZE)

    # Makespan >= completion of every job on last machine
    for j in jobs:
        model.addConstr(makespan >= C[j, n_machines - 1], name=f"mksp_{j}")

    # Completion time >= processing time (each job starts no earlier than 0)
    for j in jobs:
        model.addConstr(C[j, 0] >= p[j][0], name=f"start_{j}_0")

    # Machine order for each job: C[j,m] >= C[j,m-1] + p[j][m]
    for j in jobs:
        for m in range(1, n_machines):
            model.addConstr(C[j, m] >= C[j, m - 1] + p[j][m], name=f"seq_{j}_{m}")

    # Disjunctive constraints: on each machine, jobs don't overlap
    # If x[i,j]=1 (i before j): C[j,m] >= C[i,m] + p[j][m]
    # If x[i,j]=0 (j before i): C[i,m] >= C[j,m] + p[i][m]
    for i in jobs:
        for j in jobs:
            if i < j:
                for m in machines:
                    model.addConstr(
                        C[j, m] >= C[i, m] + p[j][m] - BIG_M * (1 - x[i, j]),
                        name=f"disj1_{i}_{j}_{m}"
                    )
                    model.addConstr(
                        C[i, m] >= C[j, m] + p[i][m] - BIG_M * x[i, j],
                        name=f"disj2_{i}_{j}_{m}"
                    )

    # Ordering consistency: x[i,j] + x[j,i] = 1 (one must precede the other)
    for i in jobs:
        for j in jobs:
            if i < j:
                model.addConstr(x[i, j] + x[j, i] == 1, name=f"order_{i}_{j}")

    # Transitivity: x[i,j] + x[j,k] - x[i,k] <= 1
    for i in jobs:
        for j in jobs:
            if i != j:
                for k in jobs:
                    if k != i and k != j:
                        model.addConstr(
                            x[i, j] + x[j, k] - x[i, k] <= 1,
                            name=f"trans_{i}_{j}_{k}"
                        )

    # Permutation flowshop: same sequence on all machines
    # x[i,j] is shared across machines (already the case — one x per pair)

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.TIME_LIMIT:
        return {"objective": None, "status": "time_limit"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}