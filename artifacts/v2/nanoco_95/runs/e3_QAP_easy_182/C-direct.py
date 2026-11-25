import gurobipy as gp
from gurobipy import GRB

def solve(params):
    flow_flat = params["flow_matrix"]
    dist_flat = params["distance_matrix"]
    n_fac = params["num_facilities"]
    n_loc = params["num_locations"]

    n = n_fac  # square assignment: n_fac == n_loc

    flow = [[flow_flat[i * n + j] for j in range(n)] for i in range(n)]
    dist = [[dist_flat[i * n + j] for j in range(n)] for i in range(n)]

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # x[i][j] = 1 if facility i assigned to location j
    x = [[model.addVar(vtype=GRB.BINARY, name=f"x_{i}_{j}")
          for j in range(n_loc)]
         for i in range(n_fac)]

    # Each facility assigned to exactly one location
    for i in range(n_fac):
        model.addConstr(gp.quicksum(x[i][j] for j in range(n_loc)) == 1)

    # Each location holds exactly one facility
    for j in range(n_loc):
        model.addConstr(gp.quicksum(x[i][j] for i in range(n_fac)) == 1)

    # Objective: sum over all pairs (i,k) of facilities and (j,l) of locations
    # of flow[i][k] * dist[j][l] * x[i][j] * x[k][l]
    # Linearize with y[i][k][j][l] = x[i][j] * x[k][l]
    obj_terms = []
    for i in range(n_fac):
        for k in range(n_fac):
            if i == k:
                continue
            for j in range(n_loc):
                for l in range(n_loc):
                    if j == l:
                        continue
                    coeff = flow[i][k] * dist[j][l]
                    if coeff == 0:
                        continue
                    y = model.addVar(vtype=GRB.BINARY, name=f"y_{i}_{k}_{j}_{l}")
                    model.addConstr(y <= x[i][j])
                    model.addConstr(y <= x[k][l])
                    model.addConstr(y >= x[i][j] + x[k][l] - 1)
                    obj_terms.append(coeff * y)

    model.setObjective(gp.quicksum(obj_terms), GRB.MINIMIZE)
    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}