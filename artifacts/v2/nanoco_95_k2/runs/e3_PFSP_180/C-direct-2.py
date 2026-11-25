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
    # With 4 jobs, there are only 4! = 24 permutations, so we can solve
    # it exactly via MIP or by enumeration. We use a MIP formulation.
    
    # Decision variables:
    #   x[i,k] = 1 if job i is assigned to position k in the sequence
    #   C[k,m] = completion time of the job in position k on machine m
    
    BIG_M = sum(p[j][m] for j in jobs for m in machines) + 1
    
    model = gp.Model()
    model.setParam("OutputFlag", 0)
    
    # Assignment variables
    x = {}
    for i in jobs:
        for k in jobs:
            x[i, k] = model.addVar(vtype=GRB.BINARY, name=f"x_{i}_{k}")
    
    # Completion time of position k on machine m
    C = {}
    for k in jobs:
        for m in machines:
            C[k, m] = model.addVar(lb=0.0, vtype=GRB.CONTINUOUS, name=f"C_{k}_{m}")
    
    # Each job assigned to exactly one position
    for i in jobs:
        model.addConstr(gp.quicksum(x[i, k] for k in jobs) == 1)
    
    # Each position has exactly one job
    for k in jobs:
        model.addConstr(gp.quicksum(x[i, k] for i in jobs) == 1)
    
    # Processing time of position k on machine m (auxiliary variable)
    P = {}
    for k in jobs:
        for m in machines:
            P[k, m] = model.addVar(lb=0.0, vtype=GRB.CONTINUOUS, name=f"P_{k}_{m}")
            # P[k,m] = sum_i x[i,k] * p[i][m]
            model.addConstr(P[k, m] == gp.quicksum(x[i, k] * p[i][m] for i in jobs))
    
    # Completion time constraints
    # C[0, 0] = P[0, 0]
    model.addConstr(C[0, 0] == P[0, 0])
    
    # First position, subsequent machines: C[0,m] = C[0,m-1] + P[0,m]
    for m in range(1, n_machines):
        model.addConstr(C[0, m] == C[0, m - 1] + P[0, m])
    
    # First machine, subsequent positions: C[k,0] = C[k-1,0] + P[k,0]
    for k in range(1, n_jobs):
        model.addConstr(C[k, 0] == C[k - 1, 0] + P[k, 0])
    
    # General: C[k,m] >= C[k-1,m] + P[k,m]  (machine continuity)
    #          C[k,m] >= C[k,m-1] + P[k,m]   (job continuity)
    for k in range(1, n_jobs):
        for m in range(1, n_machines):
            model.addConstr(C[k, m] >= C[k - 1, m] + P[k, m])
            model.addConstr(C[k, m] >= C[k, m - 1] + P[k, m])
    
    # Makespan = completion time of last position on last machine
    makespan = model.addVar(lb=0.0, vtype=GRB.CONTINUOUS, name="makespan")
    model.addConstr(makespan == C[n_jobs - 1, n_machines - 1])
    
    model.setObjective(makespan, GRB.MINIMIZE)
    model.optimize()
    
    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.TIME_LIMIT:
        return {"objective": None, "status": "time_limit"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}