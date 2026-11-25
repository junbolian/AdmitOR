import gurobipy as gp
from gurobipy import GRB

def solve(params):
    distance = params["distance"]
    num_open = params["num_facilities_open"]

    n = len(distance)
    nodes = range(n)

    # distance may be a flat list or a list-of-lists; normalize to 2D
    if n > 0 and not hasattr(distance[0], '__len__'):
        # flat list of length n*n, row-major
        dist = [[distance[i * n + j] for j in nodes] for i in nodes]
    else:
        dist = [[distance[i][j] for j in nodes] for i in nodes]

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    x = model.addVars(nodes, vtype=GRB.BINARY, name="x")
    y = model.addVars(nodes, nodes, vtype=GRB.BINARY, name="y")

    model.setObjective(
        gp.quicksum(dist[i][j] * y[i, j] for i in nodes for j in nodes if i != j),
        GRB.MAXIMIZE
    )

    model.addConstr(gp.quicksum(x[i] for i in nodes) == num_open, name="facility_count")

    for i in nodes:
        for j in nodes:
            if i != j:
                model.addConstr(y[i, j] <= x[i], name=f"y_xi_{i}_{j}")
                model.addConstr(y[i, j] <= x[j], name=f"y_xj_{i}_{j}")
                model.addConstr(y[i, j] >= x[i] + x[j] - 1, name=f"y_lb_{i}_{j}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}