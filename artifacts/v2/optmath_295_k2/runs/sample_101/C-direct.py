import gurobipy as gp
from gurobipy import GRB

def solve(params):
    coverage_scores = params["coverage_scores"]
    num_centers = params["num_centers"]
    num_nodes = params["num_nodes"]

    nodes = range(num_nodes)

    # coverage_scores may be a list-of-lists or a dict keyed by (i,j)
    if isinstance(coverage_scores, dict):
        def score(i, j):
            return coverage_scores[(i, j)]
    else:
        def score(i, j):
            return coverage_scores[i][j]

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    x = model.addVars(nodes, vtype=GRB.BINARY, name="x")
    z = model.addVars(nodes, nodes, vtype=GRB.BINARY, name="z")

    model.setObjective(
        gp.quicksum(score(i, j) * z[i, j] for i in nodes for j in nodes if i != j),
        GRB.MAXIMIZE
    )

    model.addConstr(gp.quicksum(x[i] for i in nodes) == num_centers, name="num_centers")

    for i in nodes:
        for j in nodes:
            if i != j:
                model.addConstr(z[i, j] <= x[i], name=f"z_xi_{i}_{j}")
                model.addConstr(z[i, j] <= x[j], name=f"z_xj_{i}_{j}")
                model.addConstr(z[i, j] >= x[i] + x[j] - 1, name=f"z_both_{i}_{j}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}