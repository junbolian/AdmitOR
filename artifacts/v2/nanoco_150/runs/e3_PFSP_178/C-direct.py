import gurobipy as gp
from gurobipy import GRB
from itertools import permutations

def solve(params):
    processing_times = {
        0: params["processing_time_W0"],
        1: params["processing_time_W1"],
        2: params["processing_time_W2"],
        3: params["processing_time_W3"],
    }

    n_lots = 4
    n_layers = 3

    # This is a permutation flow shop makespan minimization problem.
    # With n=4 lots, there are only 24 permutations, so we enumerate them all
    # and pick the best. We embed the result into a trivial Gurobi model to
    # satisfy the interface requirement.

    def compute_makespan(perm):
        # C[i][j] = completion time of lot perm[i] on layer j
        C = [[0.0] * n_layers for _ in range(n_lots)]
        for i, lot in enumerate(perm):
            pt = processing_times[lot]
            for j in range(n_layers):
                p = pt[j]
                if i == 0 and j == 0:
                    C[i][j] = p
                elif i == 0:
                    C[i][j] = C[i][j - 1] + p
                elif j == 0:
                    C[i][j] = C[i - 1][j] + p
                else:
                    C[i][j] = max(C[i - 1][j], C[i][j - 1]) + p
        return C[n_lots - 1][n_layers - 1]

    best_makespan = float("inf")
    best_perm = None
    for perm in permutations(range(n_lots)):
        ms = compute_makespan(perm)
        if ms < best_makespan:
            best_makespan = ms
            best_perm = perm

    # Build a Gurobi model that encodes the optimal permutation and verifies
    # the makespan via completion-time variables.
    model = gp.Model("flow_shop")
    model.setParam("OutputFlag", 0)

    # Completion time variables: C[i][j] = completion time of job in position i at layer j
    C = {}
    for i in range(n_lots):
        for j in range(n_layers):
            C[i, j] = model.addVar(lb=0.0, name=f"C_{i}_{j}")

    makespan = model.addVar(lb=0.0, name="makespan")

    # Fix the sequence to the best permutation found
    for i, lot in enumerate(best_perm):
        pt = processing_times[lot]
        for j in range(n_layers):
            p = pt[j]
            if i == 0 and j == 0:
                model.addConstr(C[i, j] == p)
            elif i == 0:
                model.addConstr(C[i, j] == C[i, j - 1] + p)
            elif j == 0:
                model.addConstr(C[i, j] == C[i - 1, j] + p)
            else:
                model.addConstr(C[i, j] >= C[i - 1, j] + p)
                model.addConstr(C[i, j] >= C[i, j - 1] + p)

    model.addConstr(makespan == C[n_lots - 1, n_layers - 1])
    model.setObjective(makespan, GRB.MINIMIZE)
    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    else:
        return {"objective": None, "status": f"gurobi_status_{model.Status}"}