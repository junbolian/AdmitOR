import gurobipy as gp
from gurobipy import GRB


def solve(params):
    flow_matrix = params["flow_matrix"]
    distance_matrix = params["distance_matrix"]
    num_facilities = params["num_facilities"]
    num_locations = params["num_locations"]

    n = num_facilities  # == num_locations by problem statement

    model = gp.Model("qap")
    model.setParam("OutputFlag", 0)

    # x[i, j] = 1 if rack i is assigned to slot j
    x = model.addVars(n, n, vtype=GRB.BINARY, name="x")

    # Each rack assigned to exactly one slot
    for i in range(n):
        model.addConstr(gp.quicksum(x[i, j] for j in range(n)) == 1, name=f"rack_{i}")

    # Each slot receives exactly one rack
    for j in range(n):
        model.addConstr(gp.quicksum(x[i, j] for i in range(n)) == 1, name=f"slot_{j}")

    # Objective: minimize sum over all rack pairs (i, k) and slot pairs (j, l)
    # of flow[i][k] * distance[j][l] * x[i,j] * x[k,l]
    # Linearize the quadratic: introduce y[i, k, j, l] = x[i,j] * x[k,l]
    # For i != k only (diagonal flow is 0, but we sum all for generality)
    # To keep it tractable at n=4, use the quadratic objective directly.

    obj = gp.QuadExpr()
    for i in range(n):
        for k in range(n):
            if i == k:
                continue
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
                    obj += f_ik * d_jl * x[i, j] * x[k, l]

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
        return {"objective": None, "status": f"gurobi_status_{status}"}