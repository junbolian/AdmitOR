import gurobipy as gp
from gurobipy import GRB

def solve(params):
    pt = {}
    for i in range(3):
        for j in range(3):
            pt[i, j] = params[f"pt_{i}_{j}"]

    BIG_M = sum(pt[i, j] for i in range(3) for j in range(3)) + 1000

    model = gp.Model("flowshop")
    model.setParam("OutputFlag", 0)

    # Start times: s[i,j] = start time of batch i on station j
    s = {}
    for i in range(3):
        for j in range(3):
            s[i, j] = model.addVar(lb=0.0, name=f"s_{i}_{j}")

    # Makespan
    cmax = model.addVar(lb=0.0, name="cmax")

    # Binary: y[i,k,j] = 1 if batch i precedes batch k on station j
    y = {}
    for i in range(3):
        for k in range(3):
            if i != k:
                for j in range(3):
                    y[i, k, j] = model.addVar(vtype=GRB.BINARY, name=f"y_{i}_{k}_{j}")

    model.update()

    # Technological order: each batch must finish on station j before starting on j+1
    for i in range(3):
        for j in range(2):
            model.addConstr(s[i, j] + pt[i, j] <= s[i, j + 1],
                            name=f"tech_{i}_{j}")

    # No overlap on each station: for each pair (i,k) and station j,
    # either i before k or k before i
    for i in range(3):
        for k in range(3):
            if i < k:
                for j in range(3):
                    # i before k on station j
                    model.addConstr(
                        s[i, j] + pt[i, j] <= s[k, j] + BIG_M * (1 - y[i, k, j]),
                        name=f"seq1_{i}_{k}_{j}"
                    )
                    # k before i on station j
                    model.addConstr(
                        s[k, j] + pt[k, j] <= s[i, j] + BIG_M * y[i, k, j],
                        name=f"seq2_{i}_{k}_{j}"
                    )

    # Makespan >= completion of every batch on station 2
    for i in range(3):
        model.addConstr(s[i, 2] + pt[i, 2] <= cmax, name=f"cmax_{i}")

    model.setObjective(cmax, GRB.MINIMIZE)
    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.TIME_LIMIT:
        return {"objective": None, "status": "time_limit"}
    else:
        return {"objective": None, "status": f"gurobi_status_{model.Status}"}