import gurobipy as gp
from gurobipy import GRB

def solve(params):
    distance_matrix = params["distance_matrix"]
    approved_edges = params["approved_edges"]

    n = len(distance_matrix)
    nodes = list(range(n))

    edges = []
    seen = set()
    for e in approved_edges:
        i, j = int(e[0]), int(e[1])
        if i == j:
            continue
        if i > j:
            i, j = j, i
        key = (i, j)
        if key not in seen:
            seen.add(key)
            edges.append(key)

    E = list(range(len(edges)))

    incident = {k: [] for k in nodes}
    for idx, (i, j) in enumerate(edges):
        incident[i].append(idx)
        incident[j].append(idx)

    model = gp.Model("max_leaf_spanning_tree")
    model.setParam("OutputFlag", 0)

    x = model.addVars(E, vtype=GRB.BINARY, name="x")
    leaf = model.addVars(nodes, vtype=GRB.BINARY, name="leaf")

    arcs = []
    for idx, (i, j) in enumerate(edges):
        arcs.append((i, j, idx))
        arcs.append((j, i, idx))
    y = model.addVars(arcs, lb=0.0, name="y")

    model.addConstr(gp.quicksum(x[idx] for idx in E) == n - 1, name="tree_size")

    root = nodes[0]
    for k in nodes:
        out_flow = gp.quicksum(y[u, v, idx] for (u, v, idx) in arcs if u == k)
        in_flow = gp.quicksum(y[u, v, idx] for (u, v, idx) in arcs if v == k)
        if k == root:
            model.addConstr(out_flow - in_flow == n - 1, name=f"flow_root_{k}")
        else:
            model.addConstr(in_flow - out_flow == 1, name=f"flow_node_{k}")

    for idx, (i, j) in enumerate(edges):
        model.addConstr(
            y[i, j, idx] + y[j, i, idx] <= (n - 1) * x[idx],
            name=f"link_{idx}",
        )

    for k in nodes:
        deg_k = gp.quicksum(x[idx] for idx in incident[k])
        model.addConstr(leaf[k] <= deg_k, name=f"leaf_lo_{k}")
        model.addConstr(deg_k <= 1 + (n - 1) * (1 - leaf[k]), name=f"leaf_hi_{k}")

    model.setObjective(gp.quicksum(leaf[k] for k in nodes), GRB.MAXIMIZE)
    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    if model.status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    return {"objective": None, "status": f"status_{model.status}"}