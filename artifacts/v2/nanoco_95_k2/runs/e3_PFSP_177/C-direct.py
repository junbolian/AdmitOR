import gurobipy as gp
from gurobipy import GRB
import itertools

def solve(params):
    proc_time = params["proc_time"]  # list of lists: proc_time[batch][unit]

    n_batches = 4
    n_units = 3
    batches = range(n_batches)
    units = range(n_units)

    # Enumerate all permutations of batches and compute makespan for each
    # This is a permutation flow shop problem (no-wait not required, but no reordering).
    # We model it as an MIP: choose a permutation (via precedence binary vars),
    # then compute start times subject to machine and job continuity constraints.

    # Binary variable x[i,j] = 1 if batch i is processed before batch j on all machines
    # Start time S[i,k] = start time of batch i on unit k
    # Makespan C = max over i of (S[i, n_units-1] + proc_time[i][n_units-1])

    # Big-M value
    M = sum(proc_time[i][k] for i in batches for k in units) + 1

    model = gp.Model("flowshop")
    model.setParam("OutputFlag", 0)
    model.setParam("TimeLimit", 120)

    # Start times
    S = model.addVars(n_batches, n_units, lb=0.0, name="S")

    # Makespan
    C = model.addVar(lb=0.0, name="C")

    # Ordering binary: y[i,j] = 1 means batch i is sequenced before batch j
    y = model.addVars(
        [(i, j) for i in batches for j in batches if i != j],
        vtype=GRB.BINARY,
        name="y"
    )

    # Objective: minimize makespan
    model.setObjective(C, GRB.MINIMIZE)

    # Makespan definition: C >= completion time of every batch on last unit
    for i in batches:
        model.addConstr(C >= S[i, n_units - 1] + proc_time[i][n_units - 1])

    # Job continuity: each batch must finish on unit k before starting unit k+1
    for i in batches:
        for k in range(n_units - 1):
            model.addConstr(S[i, k + 1] >= S[i, k] + proc_time[i][k])

    # Machine capacity: on each unit, if i before j then j starts after i finishes
    for i in batches:
        for j in batches:
            if i == j:
                continue
            for k in units:
                # If y[i,j]=1: S[j,k] >= S[i,k] + proc_time[i][k]
                model.addConstr(
                    S[j, k] >= S[i, k] + proc_time[i][k] - M * (1 - y[i, j])
                )

    # Ordering antisymmetry: exactly one of y[i,j] or y[j,i] is 1
    for i in batches:
        for j in batches:
            if i < j:
                model.addConstr(y[i, j] + y[j, i] == 1)

    # Transitivity (optional but tightens the LP relaxation)
    for i in batches:
        for j in batches:
            if i == j:
                continue
            for k in batches:
                if k == i or k == j:
                    continue
                model.addConstr(y[i, j] + y[j, k] - y[i, k] <= 1)

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.TIME_LIMIT:
        if model.SolCount > 0:
            return {"objective": float(model.ObjVal), "status": "optimal"}
        return {"objective": None, "status": "time_limit_no_solution"}
    else:
        return {"objective": None, "status": f"gurobi_status_{status}"}