import gurobipy as gp
from gurobipy import GRB

def solve(params):
    device_coordinates = params["device_coordinates"]
    distance_matrix = params["distance_matrix"]
    max_degree = params["max_degree"]

    n = len(device_coordinates)
    nodes = list(range(n))
    edges = [(i, j) for i in nodes for j in nodes if i < j]

    dist = {(i, j): distance_matrix[i][j] for (i, j) in edges}

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Binary variable: edge (i,j) selected
    x = model.addVars(edges, vtype=GRB.BINARY, name="x")

    # Minimize total cable cost
    model.setObjective(gp.quicksum(dist[e] * x[e] for e in edges), GRB.MINIMIZE)

    # Spanning tree has exactly n-1 edges
    model.addConstr(gp.quicksum(x[e] for e in edges) == n - 1, name="tree_size")

    # Degree constraint
    for i in nodes:
        incident = [e for e in edges if i in e]
        model.addConstr(gp.quicksum(x[e] for e in incident) <= max_degree, name=f"deg_{i}")

    # Single-commodity flow for connectivity (root = node 0)
    # Directed flow variables for each undirected edge
    arcs = [(i, j) for i in nodes for j in nodes if i != j]
    f = model.addVars(arcs, lb=0.0, ub=n - 1, name="f")

    # Flow on arc (i,j) or (j,i) only if edge (min,max) is selected
    for (i, j) in edges:
        model.addConstr(f[i, j] + f[j, i] <= (n - 1) * x[i, j], name=f"cap_{i}_{j}")

    # Flow balance: for each node v,
    #   outflow - inflow = supply(v)
    #   supply(root) = n-1, supply(others) = -1
    for v in nodes:
        supply = (n - 1) if v == 0 else -1
        model.addConstr(
            gp.quicksum(f[v, u] for u in nodes if u != v)
            - gp.quicksum(f[u, v] for u in nodes if u != v)
            == supply,
            name=f"balance_{v}"
        )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.TIME_LIMIT:
        return {"objective": None, "status": "time_limit"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}