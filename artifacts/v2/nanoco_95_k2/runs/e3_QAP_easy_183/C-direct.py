import gurobipy as gp
from gurobipy import GRB

def solve(params):
    flow_01 = params["flow_01"]
    flow_02 = params["flow_02"]
    flow_03 = params["flow_03"]
    flow_12 = params["flow_12"]
    flow_13 = params["flow_13"]
    flow_23 = params["flow_23"]

    dist_01 = params["dist_01"]
    dist_02 = params["dist_02"]
    dist_03 = params["dist_03"]
    dist_12 = params["dist_12"]
    dist_13 = params["dist_13"]
    dist_23 = params["dist_23"]

    # Flow matrix (symmetric, zero diagonal)
    flow = {
        (0, 1): flow_01, (1, 0): flow_01,
        (0, 2): flow_02, (2, 0): flow_02,
        (0, 3): flow_03, (3, 0): flow_03,
        (1, 2): flow_12, (2, 1): flow_12,
        (1, 3): flow_13, (3, 1): flow_13,
        (2, 3): flow_23, (3, 2): flow_23,
        (0, 0): 0, (1, 1): 0, (2, 2): 0, (3, 3): 0,
    }

    # Distance matrix (symmetric, zero diagonal)
    dist = {
        (0, 1): dist_01, (1, 0): dist_01,
        (0, 2): dist_02, (2, 0): dist_02,
        (0, 3): dist_03, (3, 0): dist_03,
        (1, 2): dist_12, (2, 1): dist_12,
        (1, 3): dist_13, (3, 1): dist_13,
        (2, 3): dist_23, (3, 2): dist_23,
        (0, 0): 0, (1, 1): 0, (2, 2): 0, (3, 3): 0,
    }

    n = 4
    departments = range(n)
    zones = range(n)

    model = gp.Model("mall_layout")
    model.setParam("OutputFlag", 0)

    # x[i, k] = 1 if department i is assigned to zone k
    x = model.addVars(departments, zones, vtype=GRB.BINARY, name="x")

    # Each department assigned to exactly one zone
    for i in departments:
        model.addConstr(gp.quicksum(x[i, k] for k in zones) == 1)

    # Each zone gets exactly one department
    for k in zones:
        model.addConstr(gp.quicksum(x[i, k] for i in departments) == 1)

    # Objective: minimize sum over all department pairs (i,j) and zone pairs (k,l)
    # of flow[i,j] * dist[k,l] * x[i,k] * x[j,l]
    # This is a quadratic objective (QP/MIQP).
    obj = gp.QuadExpr()
    for i in departments:
        for j in departments:
            if i == j:
                continue
            for k in zones:
                for l in zones:
                    if k == l:
                        continue
                    coeff = flow[(i, j)] * dist[(k, l)]
                    if coeff != 0:
                        obj += coeff * x[i, k] * x[j, l]

    # Each pair (i,j) and (j,i) both appear; divide by 2 to avoid double counting
    model.setObjective(obj * 0.5, GRB.MINIMIZE)

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver_status_{status}"}