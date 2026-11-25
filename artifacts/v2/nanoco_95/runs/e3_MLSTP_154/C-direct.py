import gurobipy as gp
from gurobipy import GRB

def solve(params):
    edge_weights = params["edge_weights"]

    # Graph structure
    n_nodes = 12
    edges = [
        (3, 7), (1, 6), (0, 8), (1, 9), (2, 8), (4, 5), (5, 9),
        (4, 11), (9, 10), (0, 10), (2, 7), (1, 5), (1, 11), (4, 7),
        (3, 8), (5, 11), (8, 10), (0, 9), (0, 6), (2, 3), (6, 9)
    ]
    n_edges = len(edges)  # 21

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # x[e] = 1 if edge e is in the spanning tree
    x = model.addVars(n_edges, vtype=GRB.BINARY, name="x")

    # Spanning tree must have exactly n_nodes - 1 edges
    model.addConstr(gp.quicksum(x[e] for e in range(n_edges)) == n_nodes - 1, name="tree_size")

    # Degree of each node
    deg = {}
    for v in range(n_nodes):
        incident = [e for e, (u, w) in enumerate(edges) if u == v or w == v]
        deg[v] = gp.quicksum(x[e] for e in incident)

    # Subtour elimination via Miller-Tucker-Zemlin style flow formulation
    # Use a directed flow: root at node 0, each non-root node gets exactly 1 unit of flow
    # from its parent. We model this with directed edge variables.

    # Directed versions of each undirected edge
    # f[e, d] where d=0 means flow in direction (u->v), d=1 means (v->u)
    f = model.addVars(n_edges, 2, vtype=GRB.CONTINUOUS, lb=0.0, name="f")

    # Flow on a directed arc can only exist if the undirected edge is selected
    # and at most (n_nodes - 1) units total can flow
    for e in range(n_edges):
        model.addConstr(f[e, 0] <= (n_nodes - 1) * x[e])
        model.addConstr(f[e, 1] <= (n_nodes - 1) * x[e])

    # Flow conservation: root (node 0) sends out (n_nodes - 1) units total
    # Each other node receives exactly 1 more unit than it sends out
    for v in range(n_nodes):
        # out-flow minus in-flow
        out_flow = gp.LinExpr()
        in_flow = gp.LinExpr()
        for e, (u, w) in enumerate(edges):
            if u == v:
                out_flow += f[e, 0]  # v -> w
                in_flow += f[e, 1]   # w -> v
            if w == v:
                out_flow += f[e, 1]  # v -> u
                in_flow += f[e, 0]   # u -> v
        if v == 0:
            # Root sends out (n_nodes - 1) net units
            model.addConstr(out_flow - in_flow == n_nodes - 1)
        else:
            # Each non-root node is a net receiver of 1 unit
            model.addConstr(in_flow - out_flow == 1)

    # Leaf indicator: is_leaf[v] = 1 if deg[v] == 1
    is_leaf = model.addVars(n_nodes, vtype=GRB.BINARY, name="is_leaf")

    # is_leaf[v] = 1 iff deg[v] = 1
    # deg[v] in [1, n_nodes-1] when node is in the tree (always, since spanning)
    # is_leaf[v] <= 1 means deg[v] >= 1 (always true in spanning tree)
    # is_leaf[v] = 1 => deg[v] <= 1 => deg[v] = 1
    # is_leaf[v] = 0 => deg[v] >= 2
    for v in range(n_nodes):
        # If is_leaf[v] = 1, then deg[v] <= 1
        model.addConstr(deg[v] <= 1 + (n_nodes - 1) * (1 - is_leaf[v]))
        # If is_leaf[v] = 0, then deg[v] >= 2
        model.addConstr(deg[v] >= 2 - (2 - 1) * is_leaf[v])
        # Equivalently: deg[v] >= 2*(1 - is_leaf[v])
        # But more precisely: deg[v] >= 2 - is_leaf[v]  since deg>=1 always
        # Let's use: deg[v] >= 2*(1 - is_leaf[v]) + 1*is_leaf[v] = 2 - is_leaf[v]
        model.addConstr(deg[v] >= 2 - is_leaf[v])

    # Maximize number of leaves
    model.setObjective(gp.quicksum(is_leaf[v] for v in range(n_nodes)), GRB.MAXIMIZE)

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver_status_{status}"}