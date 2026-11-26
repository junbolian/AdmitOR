import gurobipy as gp
from gurobipy import GRB

def solve(params):
    processing_times = params["processing_times"]

    n_batches = len(processing_times)      # 5
    n_vats = len(processing_times[0])      # 3
    batches = range(n_batches)
    vats = range(n_vats)

    # p[i][j] = processing time of batch i in vat j
    p = [[processing_times[i][j] for j in vats] for i in batches]

    # Big-M for disjunctive constraints
    M = sum(p[i][j] for i in batches for j in vats) + 1

    model = gp.Model("flow_shop")
    model.setParam("OutputFlag", 0)

    # s[i][j] = start time of batch i on vat j
    s = [[model.addVar(lb=0.0, name=f"s_{i}_{j}") for j in vats] for i in batches]

    # Makespan variable
    C_max = model.addVar(lb=0.0, name="C_max")

    # y[i][k] = 1 if batch i precedes batch k on all vats (same order on all vats
    # since this is a flow shop — but we still need binary variables per vat pair)
    # For a permutation flow shop we enforce the same sequence on every vat.
    # Binary: z[i][k] = 1 means batch i comes before batch k (on every vat)
    z = {}
    for i in batches:
        for k in batches:
            if i != k:
                z[i, k] = model.addVar(vtype=GRB.BINARY, name=f"z_{i}_{k}")

    model.update()

    # Objective
    model.setObjective(C_max, GRB.MINIMIZE)

    # Makespan >= completion of every batch on the last vat
    last_vat = n_vats - 1
    for i in batches:
        model.addConstr(C_max >= s[i][last_vat] + p[i][last_vat],
                        name=f"makespan_{i}")

    # Technological order: each batch must finish vat j before starting vat j+1
    for i in batches:
        for j in range(n_vats - 1):
            model.addConstr(s[i][j + 1] >= s[i][j] + p[i][j],
                            name=f"tech_{i}_{j}")

    # Disjunctive constraints: on each vat, two batches cannot overlap
    # z[i,k]=1  =>  batch i before batch k on every vat
    # z[i,k]+z[k,i]=1  (exactly one precedes the other)
    for i in batches:
        for k in batches:
            if i < k:
                # Mutual exclusion
                model.addConstr(z[i, k] + z[k, i] == 1,
                                name=f"mutex_{i}_{k}")
                for j in vats:
                    # If i before k on vat j
                    model.addConstr(
                        s[k][j] >= s[i][j] + p[i][j] - M * (1 - z[i, k]),
                        name=f"disj_ik_{i}_{k}_{j}"
                    )
                    # If k before i on vat j
                    model.addConstr(
                        s[i][j] >= s[k][j] + p[k][j] - M * z[i, k],
                        name=f"disj_ki_{i}_{k}_{j}"
                    )

    # Flow shop: same relative order on all vats
    # If z[i,k]=1 (i before k on vat 0), then i before k on all vats
    for i in batches:
        for k in batches:
            if i < k:
                for j in vats:
                    # z[i,k]=1 => s[k][j] >= s[i][j]+p[i][j]  (already in disjunctive)
                    # We additionally enforce same ordering across vats:
                    # z[i,k] on vat 0 equals z[i,k] on every other vat — handled
                    # because z[i,k] is shared across all vat constraints above.
                    pass  # already enforced by shared z[i,k]

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver_status_{status}"}