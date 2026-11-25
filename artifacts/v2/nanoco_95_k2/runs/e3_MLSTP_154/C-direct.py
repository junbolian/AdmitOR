import gurobipy as gp
from gurobipy import GRB

def solve(params):
    distance_matrix = params["distance_matrix"]
    approved_edges = params["approved_edges"]

    n = len(distance_matrix)
    root = 0

    edge_set = set()
    for e in approved_edges:
        i = int(e[0])
        j = int(e[1])
        if i == j:
            continue
        if i > j:
            i, j = j, i
        edge_set.add((i, j))

    edges = sorted(edge_set)

    adj = [[] for _ in range(n)]
    arcs = []
    for i, j in edges:
        adj[i].append(j)
        adj[j].append(i)
        arcs.append((i, j))
        arcs.append((j, i))

    model = gp.Model("max_leaf_spanning_tree")
    model.Params.OutputFlag = 0

    y = model.addVars(arcs, vtype=GRB.BINARY, name="y")
    f = model.addVars(arcs, lb=0.0, ub=max(n - 1, 1), name="f")

    for i, j in edges:
        model.addConstr(y[i, j] + y[j, i] <= 1, name=f"select_{i}_{j}")

    model.addConstr(gp.quicksum(y[a] for a in arcs) == n - 1, name="tree_size")

    for v in range(n):
        out_flow = gp.quicksum(f[v, w] for w in adj[v])
        in_flow = gp.quicksum(f[w, v] for w in adj[v])
        if v == root:
            model.addConstr(out_flow - in_flow == n - 1, name="flow_root")
        else:
            model.addConstr(out_flow - in_flow == -1, name=f"flow_node_{v}")

    for a in arcs:
        model.addConstr(f[a] <= (n - 1) * y[a], name=f"cap_{a[0]}_{a[1]}")
        model.addConstr(f[a] >= y[a], name=f"use_{a[0]}_{a[1]}")

    z = model.addVars(n, vtype=GRB.BINARY, name="z")
    for v in range(n):
        deg = gp.quicksum(y[v, w] for w in adj[v]) + gp.quicksum(y[w, v] for w in adj[v])
        model.addConstr(z[v] <= deg, name=f"leaf_lower_{v}")
        model.addConstr(z[v] + deg <= 2, name=f"leaf_upper_{v}")

    model.setObjective(gp.quicksum(z[v] for v in range(n)), GRB.MAXIMIZE)
    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    if model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    if model.Status == GRB.INF_OR_UNBD:
        return {"objective": None, "status": "infeasible_or_unbounded"}
    return {"objective": None, "status": f"gurobi_status_{model.Status}"}