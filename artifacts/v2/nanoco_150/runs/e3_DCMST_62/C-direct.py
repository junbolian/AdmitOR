import gurobipy as gp
from gurobipy import GRB
import math

def solve(params):
    n = 12
    dist = params["distance_matrix"]
    max_deg = params["max_degree"]

    # Build edge list (undirected, i < j)
    edges = [(i, j) for i in range(n) for j in range(i+1, n)]

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Binary variable: edge (i,j) selected
    x = model.addVars(edges, vtype=GRB.BINARY, name="x")

    # Objective: minimize total wire length
    model.setObjective(
        gp.quicksum(dist[i][j] * x[i, j] for i, j in edges),
        GRB.MINIMIZE
    )

    # Exactly n-1 edges (tree has n-1 edges)
    model.addConstr(gp.quicksum(x[i, j] for i, j in edges) == n - 1, name="tree_size")

    # Degree constraint: each node at most max_deg connections
    for k in range(n):
        node_edges = [(i, j) for (i, j) in edges if i == k or j == k]
        model.addConstr(
            gp.quicksum(x[i, j] for i, j in node_edges) <= max_deg,
            name=f"deg_{k}"
        )

    # Subtour elimination via Miller-Tucker-Zemlin (MTZ) formulation
    # We root the tree at node 0 and assign ordering labels u[i] for i in 1..n-1
    # For connectivity in an undirected tree, we model directed arcs:
    # For each undirected edge (i,j), we have directed arcs a[i,j] and a[j,i]
    # Exactly one direction is used when the edge is selected.

    # arc variables: for each undirected edge, two directed versions
    arcs = [(i, j) for i in range(n) for j in range(n) if i != j]
    a = model.addVars(arcs, vtype=GRB.BINARY, name="a")

    # Link arc variables to edge variables
    for (i, j) in edges:
        # If edge selected, exactly one direction used; if not selected, neither
        model.addConstr(a[i, j] + a[j, i] == x[i, j], name=f"arc_link_{i}_{j}")

    # Flow-based connectivity: node 0 is root
    # Each non-root node must have exactly one incoming arc (from its parent)
    for k in range(1, n):
        in_arcs = [(i, k) for i in range(n) if i != k]
        model.addConstr(
            gp.quicksum(a[i, k] for (i, k2) in in_arcs if k2 == k) == 1,
            name=f"one_parent_{k}"
        )

    # Root has no incoming arc
    model.addConstr(
        gp.quicksum(a[i, 0] for i in range(1, n)) == 0,
        name="root_no_parent"
    )

    # MTZ subtour elimination
    u = model.addVars(range(n), lb=0.0, ub=n - 1.0, vtype=GRB.CONTINUOUS, name="u")
    model.addConstr(u[0] == 0, name="root_label")

    for (i, j) in arcs:
        if j != 0:  # skip arcs into root
            model.addConstr(
                u[i] - u[j] + n * a[i, j] <= n - 1,
                name=f"mtz_{i}_{j}"
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