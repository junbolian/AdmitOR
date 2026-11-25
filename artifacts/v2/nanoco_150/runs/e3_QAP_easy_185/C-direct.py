import gurobipy as gp
from gurobipy import GRB

def solve(params):
    flow = {
        (0,1): params["flow_01"], (0,2): params["flow_02"],
        (0,3): params["flow_03"], (0,4): params["flow_04"],
        (1,2): params["flow_12"], (1,3): params["flow_13"],
        (1,4): params["flow_14"], (2,3): params["flow_23"],
        (2,4): params["flow_24"], (3,4): params["flow_34"],
    }
    dist = {
        (0,1): params["dist_01"], (0,2): params["dist_02"],
        (0,3): params["dist_03"], (0,4): params["dist_04"],
        (1,2): params["dist_12"], (1,3): params["dist_13"],
        (1,4): params["dist_14"], (2,3): params["dist_23"],
        (2,4): params["dist_24"], (3,4): params["dist_34"],
    }

    n = 5
    divisions = range(n)
    sites = range(n)

    # Build symmetric lookups
    def get_flow(i, j):
        if i == j:
            return 0.0
        key = (min(i,j), max(i,j))
        return flow[key]

    def get_dist(p, q):
        if p == q:
            return 0.0
        key = (min(p,q), max(p,q))
        return dist[key]

    model = gp.Model("QAP")
    model.setParam("OutputFlag", 0)

    # x[i,p] = 1 if division i is assigned to site p
    x = model.addVars(divisions, sites, vtype=GRB.BINARY, name="x")

    # Each division assigned to exactly one site
    for i in divisions:
        model.addConstr(gp.quicksum(x[i, p] for p in sites) == 1, name=f"div_{i}")

    # Each site holds exactly one division
    for p in sites:
        model.addConstr(gp.quicksum(x[i, p] for i in divisions) == 1, name=f"site_{p}")

    # Linearize the quadratic objective with auxiliary variables
    # y[i,j,p,q] = x[i,p] * x[j,q], only for i < j
    pairs_div = [(i, j) for i in divisions for j in divisions if i < j]
    pairs_site = [(p, q) for p in sites for q in sites if p != q]

    y = model.addVars(
        [(i, j, p, q) for (i,j) in pairs_div for p in sites for q in sites if p != q],
        vtype=GRB.BINARY, name="y"
    )

    for (i, j) in pairs_div:
        for p in sites:
            for q in sites:
                if p == q:
                    continue
                # y[i,j,p,q] = x[i,p] * x[j,q]
                model.addConstr(y[i, j, p, q] <= x[i, p])
                model.addConstr(y[i, j, p, q] <= x[j, q])
                model.addConstr(y[i, j, p, q] >= x[i, p] + x[j, q] - 1)

    obj = gp.LinExpr()
    for (i, j) in pairs_div:
        f_ij = get_flow(i, j)
        if f_ij == 0:
            continue
        for p in sites:
            for q in sites:
                if p == q:
                    continue
                d_pq = get_dist(p, q)
                if d_pq == 0:
                    continue
                obj += f_ij * d_pq * y[i, j, p, q]

    model.setObjective(obj, GRB.MINIMIZE)
    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.TIME_LIMIT:
        return {"objective": None, "status": "time_limit"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}