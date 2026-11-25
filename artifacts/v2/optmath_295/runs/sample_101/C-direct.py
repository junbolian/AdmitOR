import gurobipy as gp
from gurobipy import GRB

def solve(params):
    coverage_scores = params["coverage_scores"]
    num_centers = params["num_centers"]

    n = 5
    nodes = range(n)

    # Build d[i][j] from row-major order over ordered pairs (i,j), i != j
    d = {}
    idx = 0
    for i in nodes:
        for j in nodes:
            if i != j:
                d[i, j] = coverage_scores[idx]
                idx += 1

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    x = model.addVars(nodes, vtype=GRB.BINARY, name="x")
    z = model.addVars(
        [(i, j) for i in nodes for j in nodes if i != j],
        vtype=GRB.BINARY,
        name="z"
    )

    # Maximize total pairwise coverage effectiveness
    model.setObjective(
        gp.quicksum(d[i, j] * z[i, j] for i in nodes for j in nodes if i != j),
        GRB.MAXIMIZE
    )

    # Exactly num_centers centers
    model.addConstr(gp.quicksum(x[i] for i in nodes) == num_centers, name="num_centers")

    # Pairwise coverage logic: z[i,j] = 1 iff x[i]=1 and x[j]=1
    for i in nodes:
        for j in nodes:
            if i != j:
                model.addConstr(z[i, j] <= x[i], name=f"z_xi_{i}_{j}")
                model.addConstr(z[i, j] <= x[j], name=f"z_xj_{i}_{j}")
                model.addConstr(z[i, j] >= x[i] + x[j] - 1, name=f"z_lb_{i}_{j}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}