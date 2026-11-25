import gurobipy as gp
from gurobipy import GRB
from itertools import permutations

def solve(params):
    p = params["p"]  # p[j][m]: processing time of job j on machine m
    
    n_jobs = len(p)
    n_machines = len(p[0])
    jobs = list(range(n_jobs))
    machines = list(range(n_machines))
    
    # This is a permutation flowshop makespan minimization problem.
    # With 4 jobs, we can enumerate all 4! = 24 permutations and pick the best,
    # but we'll use a MIP formulation as required by gurobipy.
    #
    # Decision variables:
    #   x[j,k] = 1 if job j is assigned to position k in the sequence
    #   C[k,m]  = completion time of the job at position k on machine m
    # Makespan = max completion time at last machine across all positions

    model = gp.Model("permutation_flowshop")
    model.setParam("OutputFlag", 0)

    # x[j,k]: assignment of job j to position k
    x = model.addVars(n_jobs, n_jobs, vtype=GRB.BINARY, name="x")

    # C[k,m]: completion time of the job in position k on machine m
    # Upper bound: sum of all processing times (loose but valid)
    total_p = sum(p[j][m] for j in jobs for m in machines)
    C = model.addVars(n_jobs, n_machines, vtype=GRB.CONTINUOUS, lb=0.0,
                      ub=total_p, name="C")

    # Makespan variable
    makespan = model.addVar(vtype=GRB.CONTINUOUS, lb=0.0, ub=total_p, name="makespan")

    # Each job assigned to exactly one position
    for j in jobs:
        model.addConstr(gp.quicksum(x[j, k] for k in jobs) == 1, name=f"job_pos_{j}")

    # Each position has exactly one job
    for k in jobs:
        model.addConstr(gp.quicksum(x[j, k] for j in jobs) == 1, name=f"pos_job_{k}")

    # Completion time constraints.
    # C[k,m] >= C[k-1,m] + p[j][m] * x[j,k]  (machine continuity across positions)
    # C[k,m] >= C[k,m-1] + p[j][m] * x[j,k]  (job continuity across machines)
    # Combined: C[k,m] >= max(C[k-1,m], C[k,m-1]) + p[j][m]*x[j,k]
    #
    # We linearize using big-M: for each (k,m,j), if x[j,k]=1 then
    #   C[k,m] >= C[k-1,m] + p[j][m]  (prev position, same machine)
    #   C[k,m] >= C[k,m-1] + p[j][m]  (same position, prev machine)
    # Using: C[k,m] >= C[prev,machine] + p[j][m] - M*(1 - x[j,k])

    M_big = total_p  # big-M value

    for k in jobs:
        for m in machines:
            for j in jobs:
                # Constraint: C[k,m] >= C[k-1,m] + p[j][m] if x[j,k]=1
                if k > 0:
                    model.addConstr(
                        C[k, m] >= C[k - 1, m] + p[j][m] - M_big * (1 - x[j, k]),
                        name=f"mach_cont_{k}_{m}_{j}"
                    )
                else:
                    # First position: no predecessor position, so only machine chain matters
                    # C[0,m] >= p[j][m] if x[j,0]=1 (start from time 0 on machine chain)
                    # This is handled by the machine predecessor constraint below
                    pass

                # Constraint: C[k,m] >= C[k,m-1] + p[j][m] if x[j,k]=1
                if m > 0:
                    model.addConstr(
                        C[k, m] >= C[k, m - 1] + p[j][m] - M_big * (1 - x[j, k]),
                        name=f"job_cont_{k}_{m}_{j}"
                    )
                else:
                    # First machine: job must complete at least p[j][m] time
                    # C[k,0] >= p[j][0] if x[j,k]=1
                    model.addConstr(
                        C[k, 0] >= p[j][0] - M_big * (1 - x[j, k]),
                        name=f"first_mach_{k}_{j}"
                    )

    # Makespan >= C[k, last_machine] for all positions k
    for k in jobs:
        model.addConstr(makespan >= C[k, n_machines - 1], name=f"makespan_{k}")

    # Objective
    model.setObjective(makespan, GRB.MINIMIZE)

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.TIME_LIMIT:
        return {"objective": None, "status": "time_limit"}
    else:
        return {"objective": None, "status": f"gurobi_status_{model.Status}"}