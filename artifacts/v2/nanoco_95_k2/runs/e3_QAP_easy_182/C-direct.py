import gurobipy as gp
from gurobipy import GRB


def solve(params):
    flow_matrix = params["flow_matrix"]
    distance_matrix = params["distance_matrix"]
    num_facilities = params["num_facilities"]
    num_locations = params["num_locations"]

    n = num_facilities  # == num_locations for this balanced QAP

    model = gp.Model("qap")
    model.setParam("OutputFlag", 0)

    # x[i, j] = 1 if rack i is assigned to slot j
    x = model.addVars(n, n, vtype=GRB.BINARY, name="x")

    # Each rack assigned to exactly one slot
    for i in range(n):
        model.addConstr(gp.quicksum(x[i, j] for j in range(n)) == 1, name=f"rack_{i}")

    # Each slot holds exactly one rack
    for j in range(n):
        model.addConstr(gp.quicksum(x[i, j] for i in range(n)) == 1, name=f"slot_{j}")

    # Linearize the product x[i,j]*x[k,l] with auxiliary variable y[i,j,k,l]
    # Objective: sum_{i,k} sum_{j,l} flow[i][k] * dist[j][l] * x[i,j] * x[k,l]
    # To avoid double-counting, sum over all i<k pairs and multiply by 2,
    # or equivalently sum all (i,k,j,l) with i!=k and divide by 2 — here we
    # iterate i<k only and multiply flow contribution by 2 (symmetric matrices).

    y = {}
    obj_terms = []

    for i in range(n):
        for k in range(i + 1, n):
            f_ik = flow_matrix[i][k]
            if f_ik == 0:
                continue
            for j in range(n):
                for l in range(n):
                    if j == l:
                        continue
                    d_jl = distance_matrix[j][l]
                    if d_jl == 0:
                        continue
                    # y[i,j,k,l] = x[i,j] * x[k,l]
                    yvar = model.addVar(vtype=GRB.BINARY, name=f"y_{i}_{j}_{k}_{l}")
                    y[(i, j, k, l)] = yvar
                    model.addConstr(yvar <= x[i, j])
                    model.addConstr(yvar <= x[k, l])
                    model.addConstr(yvar >= x[i, j] + x[k, l] - 1)
                    # Symmetric: flow[i][k]==flow[k][i], dist[j][l]==dist[l][j]
                    # pair (i,k) counted once, multiply by 2 for both orderings
                    obj_terms.append(2.0 * f_ik * d_jl * yvar)

    model.setObjective(gp.quicksum(obj_terms), GRB.MINIMIZE)
    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"gurobi_status_{status}"}