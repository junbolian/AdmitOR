import gurobipy as gp
from gurobipy import GRB

def solve(params):
    flow = {
        (0,1): params["flow_01"], (1,0): params["flow_01"],
        (0,2): params["flow_02"], (2,0): params["flow_02"],
        (0,3): params["flow_03"], (3,0): params["flow_03"],
        (1,2): params["flow_12"], (2,1): params["flow_12"],
        (1,3): params["flow_13"], (3,1): params["flow_13"],
        (2,3): params["flow_23"], (3,2): params["flow_23"],
    }

    dist = {
        (0,1): params["dist_01"], (1,0): params["dist_01"],
        (0,2): params["dist_02"], (2,0): params["dist_02"],
        (0,3): params["dist_03"], (3,0): params["dist_03"],
        (1,2): params["dist_12"], (2,1): params["dist_12"],
        (1,3): params["dist_13"], (3,1): params["dist_13"],
        (2,3): params["dist_23"], (3,2): params["dist_23"],
    }

    n = 4
    depts = range(n)
    zones = range(n)

    model = gp.Model("mall_layout")
    model.setParam("OutputFlag", 0)

    # x[i,k] = 1 if department i is assigned to zone k
    x = model.addVars(depts, zones, vtype=GRB.BINARY, name="x")

    # Each department assigned to exactly one zone
    for i in depts:
        model.addConstr(gp.quicksum(x[i, k] for k in zones) == 1)

    # Each zone holds exactly one department
    for k in zones:
        model.addConstr(gp.quicksum(x[i, k] for i in depts) == 1)

    # Objective: minimize sum over all dept pairs (i,j) and zone pairs (k,l)
    # of flow[i,j] * dist[k,l] * x[i,k] * x[j,l]
    # To linearize: introduce y[i,j,k,l] = x[i,k] * x[j,l] for i<j
    # But with n=4, brute-force linearization is tractable.
    # Use the standard QAP linearization: since x[i,k]*x[j,l] is bilinear,
    # introduce z[i,k,j,l] = x[i,k] * x[j,l].

    pairs = [(i, j) for i in depts for j in depts if i < j]
    zone_pairs = [(k, l) for k in zones for l in zones if k != l]

    z = model.addVars(
        [(i, k, j, l) for (i, j) in pairs for (k, l) in zone_pairs],
        vtype=GRB.BINARY,
        name="z"
    )

    for (i, j) in pairs:
        for (k, l) in zone_pairs:
            # z[i,k,j,l] = x[i,k] * x[j,l]
            model.addConstr(z[i, k, j, l] <= x[i, k])
            model.addConstr(z[i, k, j, l] <= x[j, l])
            model.addConstr(z[i, k, j, l] >= x[i, k] + x[j, l] - 1)

    obj = gp.quicksum(
        flow[(i, j)] * dist[(k, l)] * z[i, k, j, l]
        for (i, j) in pairs
        for (k, l) in zone_pairs
    )

    model.setObjective(obj, GRB.MINIMIZE)
    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver_status_{model.Status}"}