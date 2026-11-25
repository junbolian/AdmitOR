import gurobipy as gp
from gurobipy import GRB


def solve(params):
    num_nodes = params["num_nodes"]
    num_edges = params["num_edges"]
    edge_list = params["edge_list"]
    distance_matrix = params["distance_matrix"]

    # Build model
    model = gp.Model("MaxLeafSpanningTree")
    model.setParam("OutputFlag", 0)

    n = num_nodes
    E = list(range(num_edges))
    edges = [(int(edge_list[k][0]), int(edge_list[k][1])) for k in range(num_edges)]

    # Edge selection variables
    x = model.addVars(E, vtype=GRB.BINARY, name="x")

    # Degree variables for each node
    deg = model.addVars(n, vtype=GRB.INTEGER, lb=0, name="deg")

    # Leaf indicator: leaf[i] = 1 if node i has degree exactly 1
    leaf = model.addVars(n, vtype=GRB.BINARY, name="leaf")

    # Degree definition
    for i in range(n):
        incident = [k for k in E if edges[k][0] == i or edges[k][1] == i]
        model.addConstr(deg[i] == gp.quicksum(x[k] for k in incident), name=f"deg_{i}")

    # Spanning tree: exactly n-1 edges
    model.addConstr(gp.quicksum(x[k] for k in E) == n - 1, name="tree_size")

    # Connectivity via Miller-Tucker-Zemlin (MTZ) flow formulation
    # Use a directed version: for each undirected edge, create two directed arcs
    # Route a commodity of n-1 units from a root (node 0) to all others

    # We root the tree at node 0
    # f[k][d] = flow on directed arc (u->v) or (v->u) of edge k toward node d
    # This gets expensive; instead use single-commodity flow for connectivity

    # Single-commodity flow: source node 0 sends 1 unit to each other node
    # For edge k = (u,v): flow f_uv >= 0 (u to v), f_vu >= 0 (v to u)
    f = model.addVars(E, [0, 1], vtype=GRB.CONTINUOUS, lb=0, name="f")

    # Flow capacity: flow only if edge selected
    for k in E:
        model.addConstr(f[k, 0] <= (n - 1) * x[k], name=f"cap0_{k}")
        model.addConstr(f[k, 1] <= (n - 1) * x[k], name=f"cap1_{k}")

    # Flow conservation
    for i in range(n):
        # Net flow out of node i
        outflow = gp.LinExpr()
        for k in E:
            u, v = edges[k]
            if u == i:
                outflow += f[k, 0] - f[k, 1]
            elif v == i:
                outflow += f[k, 1] - f[k, 0]

        if i == 0:
            # Source supplies n-1 units
            model.addConstr(outflow == n - 1, name=f"flow_src_{i}")
        else:
            # Every other node consumes 1 unit
            model.addConstr(outflow == -1, name=f"flow_cons_{i}")

    # Leaf node: leaf[i] = 1 iff deg[i] = 1
    # deg[i] >= 1 always (connected tree), deg[i] <= n-1
    # leaf[i] = 1 => deg[i] = 1
    # leaf[i] = 0 => deg[i] >= 2
    for i in range(n):
        # leaf[i] <= 2 - deg[i]  =>  leaf[i] + deg[i] <= 2
        # This forces leaf[i] = 0 when deg[i] >= 2
        model.addConstr(leaf[i] + deg[i] <= 2, name=f"leaf_ub_{i}")
        # leaf[i] >= 2 - deg[i]  =>  leaf[i] + deg[i] >= 2  when deg[i]=1
        # Actually: leaf[i] >= 1 when deg[i] = 1
        # Use: leaf[i] >= 2 - deg[i]
        model.addConstr(leaf[i] >= 2 - deg[i], name=f"leaf_lb_{i}")

    # Objective: maximize leaf nodes
    model.setObjective(gp.quicksum(leaf[i] for i in range(n)), GRB.MAXIMIZE)

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.TIME_LIMIT:
        return {"objective": None, "status": "time_limit"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}