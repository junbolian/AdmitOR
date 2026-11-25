import gurobipy as gp
from gurobipy import GRB


def solve(params):
    flow = params["flow_matrix"]
    dist = params["distance_matrix"]
    coords = params["room_coordinates"]
    n = params["num_units"]
    m = params["num_rooms"]

    model = gp.Model("hospital_qap")
    model.Params.OutputFlag = 0

    # x[i, r] = 1 if unit i is assigned to room r
    x = {}
    for i in range(n):
        for r in range(m):
            x[i, r] = model.addVar(vtype=GRB.BINARY, name=f"x_{i}_{r}")

    # Each unit is assigned to exactly one room
    for i in range(n):
        model.addConstr(gp.quicksum(x[i, r] for r in range(m)) == 1, name=f"unit_{i}")

    # Each room hosts exactly one unit
    for r in range(m):
        model.addConstr(gp.quicksum(x[i, r] for i in range(n)) == 1, name=f"room_{r}")

    # Quadratic objective: sum over all ordered unit pairs (i, j) and room pairs (r, s)
    # of flow[i][j] * distance[r][s] * x[i, r] * x[j, s]
    obj = gp.QuadExpr()
    for i in range(n):
        for j in range(n):
            f_ij = flow[i][j]
            if f_ij == 0:
                continue
            for r in range(m):
                for s in range(m):
                    d_rs = dist[r][s]
                    if d_rs == 0:
                        continue
                    obj += f_ij * d_rs * x[i, r] * x[j, s]

    model.setObjective(obj, GRB.MINIMIZE)
    model.Params.NonConvex = 2

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    if model.status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    return {"objective": None, "status": f"status_{model.status}"}