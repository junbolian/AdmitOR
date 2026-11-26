import gurobipy as gp
from gurobipy import GRB
import numpy as np

def solve(params):
    D_jk  = np.array(params["D_jk"],  dtype=float)  # (1000, 5)
    r_klm = np.array(params["r_klm"], dtype=float)  # (5, 3, 4)
    R_im  = np.array(params["R_im"],  dtype=float)  # (10, 4)
    c_kl  = np.array(params["c_kl"],  dtype=float)  # (5, 3)
    c_il  = np.array(params["c_il"],  dtype=float)  # (10, 3)
    P_ikl = np.array(params["P_ikl"], dtype=float)  # (10, 5, 3)
    T_ijk = np.array(params["T_ijk"], dtype=float)  # (10, 1000, 5)

    n_mills     = 10
    n_customers = 1000
    n_machines  = 3
    n_raw       = 4
    n_paper     = 5

    I = range(n_mills)
    J = range(n_customers)
    K = range(n_paper)
    L = range(n_machines)
    M = range(n_raw)

    model = gp.Model("paper_manufacturing")
    model.setParam("OutputFlag", 0)

    # x[i,k,l]: units of paper type k produced on machine l at mill i
    x = model.addVars(n_mills, n_paper, n_machines, lb=0.0, name="x")

    # y[i,j,k]: units of paper type k shipped from mill i to customer j
    y = model.addVars(n_mills, n_customers, n_paper, lb=0.0, name="y")

    # Objective: minimize total cost (transportation + production)
    # Build objective using pre-extracted coefficient arrays to avoid repeated
    # numpy indexing inside a large generator which can be slow and error-prone.
    T_flat = T_ijk.reshape(-1)
    P_flat = P_ikl.reshape(-1)

    obj_expr = gp.LinExpr()

    for i in I:
        for j in J:
            for k in K:
                coeff = float(T_ijk[i, j, k])
                obj_expr.add(y[i, j, k], coeff)

    for i in I:
        for k in K:
            for l in L:
                coeff = float(P_ikl[i, k, l])
                obj_expr.add(x[i, k, l], coeff)

    model.setObjective(obj_expr, GRB.MINIMIZE)

    # 1. Demand satisfaction: total shipped to customer j of paper type k >= demand
    for j in J:
        for k in K:
            model.addConstr(
                gp.quicksum(y[i, j, k] for i in I) >= float(D_jk[j, k]),
                name=f"demand_{j}_{k}"
            )

    # 2. Flow balance: total shipped from mill i of paper type k
    #    <= total produced at mill i of paper type k (across all machines)
    for i in I:
        for k in K:
            model.addConstr(
                gp.quicksum(y[i, j, k] for j in J) <= gp.quicksum(x[i, k, l] for l in L),
                name=f"flow_{i}_{k}"
            )

    # 3. Machine time capacity at mill i for machine l
    for i in I:
        for l in L:
            model.addConstr(
                gp.quicksum(float(c_kl[k, l]) * x[i, k, l] for k in K) <= float(c_il[i, l]),
                name=f"machine_{i}_{l}"
            )

    # 4. Raw material availability at mill i for material m
    for i in I:
        for m in M:
            model.addConstr(
                gp.quicksum(float(r_klm[k, l, m]) * x[i, k, l] for k in K for l in L) <= float(R_im[i, m]),
                name=f"rawmat_{i}_{m}"
            )

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"gurobi_status_{status}"}