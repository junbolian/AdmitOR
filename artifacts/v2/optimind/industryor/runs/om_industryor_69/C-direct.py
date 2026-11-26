import gurobipy as gp
from gurobipy import GRB

def solve(params):
    d12 = params["d12"]
    d21 = params["d21"]
    c11 = params["c11"]
    c12 = params["c12"]
    c21 = params["c21"]
    c22 = params["c22"]

    # x[i][p] = 1 if factory i is assigned to location p
    # i in {1,2}, p in {1,2}
    # Quadratic Assignment Problem with n=2

    model = gp.Model("QAP_n2")
    model.setParam("OutputFlag", 0)

    # Decision variables: x[i,p] = 1 if factory i assigned to location p
    x = {}
    for i in range(1, 3):
        for p in range(1, 3):
            x[i, p] = model.addVar(vtype=GRB.BINARY, name=f"x_{i}_{p}")

    # Each factory assigned to exactly one location
    for i in range(1, 3):
        model.addConstr(gp.quicksum(x[i, p] for p in range(1, 3)) == 1, name=f"factory_{i}_assign")

    # Each location gets exactly one factory
    for p in range(1, 3):
        model.addConstr(gp.quicksum(x[i, p] for i in range(1, 3)) == 1, name=f"location_{p}_assign")

    # d values: d[i,j] is transportation volume from factory i to factory j
    # d12 and d21 are given; d11 and d22 are not given (self-transport, assumed 0)
    d = {(1, 2): d12, (2, 1): d21, (1, 1): 0.0, (2, 2): 0.0}

    # c[p,q] is unit cost from location p to location q
    c = {(1, 1): c11, (1, 2): c12, (2, 1): c21, (2, 2): c22}

    # Objective: minimize sum over i,j,p,q of d[i,j] * c[p,q] * x[i,p] * x[j,q]
    # Linearize: introduce y[i,j,p,q] = x[i,p] * x[j,q] for i!=j
    obj_expr = gp.QuadExpr()
    for i in range(1, 3):
        for j in range(1, 3):
            if i == j:
                continue
            for p in range(1, 3):
                for q in range(1, 3):
                    obj_expr += d[i, j] * c[p, q] * x[i, p] * x[j, q]

    model.setObjective(obj_expr, GRB.MINIMIZE)

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}