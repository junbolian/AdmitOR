import gurobipy as gp
from gurobipy import GRB

def solve(params):
    # Try multiple possible key names for the transportation quantity matrix
    d = params.get("d", params.get("d_ij", params.get("flow", None)))
    # Try multiple possible key names for the unit transportation cost matrix
    c = params.get("c", params.get("c_pq", params.get("cost", None)))

    if d is None:
        # Try to infer from available keys
        for key in params:
            if key.lower().startswith("d"):
                d = params[key]
                break
    if c is None:
        for key in params:
            if key.lower().startswith("c"):
                c = params[key]
                break

    if d is None or c is None:
        return {"objective": None, "status": "missing_params"}

    n = len(d)
    locations = range(n)
    factories = range(n)

    model = gp.Model("QAP")
    model.setParam("OutputFlag", 0)

    # x[i][p] = 1 if factory i is assigned to location p
    x = [[model.addVar(vtype=GRB.BINARY, name=f"x_{i}_{p}") for p in locations] for i in factories]

    # Each factory assigned to exactly one location
    for i in factories:
        model.addConstr(gp.quicksum(x[i][p] for p in locations) == 1, name=f"factory_{i}")

    # Each location assigned to exactly one factory
    for p in locations:
        model.addConstr(gp.quicksum(x[i][p] for i in factories) == 1, name=f"location_{p}")

    # Objective: minimize sum over i,j,p,q of d[i][j] * c[p][q] * x[i][p] * x[j][q]
    # Linearize: introduce y[i][j][p][q] = x[i][p] * x[j][q]
    obj = gp.LinExpr()

    y = {}
    for i in factories:
        for j in factories:
            for p in locations:
                for q in locations:
                    cost = d[i][j] * c[p][q]
                    if cost == 0:
                        continue
                    var = model.addVar(vtype=GRB.BINARY, name=f"y_{i}_{j}_{p}_{q}")
                    y[(i, j, p, q)] = var
                    obj += cost * var
                    # Linearization constraints for y = x[i][p] * x[j][q]
                    model.addConstr(var <= x[i][p], name=f"yl1_{i}_{j}_{p}_{q}")
                    model.addConstr(var <= x[j][q], name=f"yl2_{i}_{j}_{p}_{q}")
                    model.addConstr(var >= x[i][p] + x[j][q] - 1, name=f"yl3_{i}_{j}_{p}_{q}")

    model.setObjective(obj, GRB.MINIMIZE)

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