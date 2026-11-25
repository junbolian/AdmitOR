import gurobipy as gp
from gurobipy import GRB

def solve(params):
    n = int(params["num_branches"])
    max_deg = params["max_degree"]

    # Build cost dict for all pairs (i,j) with i < j, 1-indexed
    def get_cost(i, j):
        if i > j:
            i, j = j, i
        if j <= 9:
            key = f"cost_{i}{j}"
        elif i <= 9:
            key = f"cost_{i}_{j}"
        else:
            key = f"cost_{i}_{j}"
        return params[key]

    edges = [(i, j) for i in range(1, n + 1) for j in range(i + 1, n + 1)]
    cost = {(i, j): get_cost(i, j) for (i, j) in edges}

    model = gp.Model("min_cost_spanning_tree_degree_constrained")
    model.setParam("OutputFlag", 0)

    # Binary variable: x[i,j] = 1 if edge (i,j) is in the tree
    x = model.addVars(edges, vtype=GRB.BINARY, name="x")

    # Objective: minimize total cost
    model.setObjective(gp.quicksum(cost[e] * x[e] for e in edges), GRB.MINIMIZE)

    # A spanning tree on n nodes has exactly n-1 edges
    model.addConstr(gp.quicksum(x[e] for e in edges) == n - 1, name="tree_size")

    # Degree constraint: each node has at most max_deg edges
    for node in range(1, n + 1):
        incident = [e for e in edges if node in e]
        model.addConstr(gp.quicksum(x[e] for e in incident) <= max_deg, name=f"deg_{node}")

    # Connectivity via subtour elimination (Miller-Tucker-Zemlin style won't work
    # directly for trees; use flow-based formulation instead).
    # We use a single-commodity flow approach rooted at node 1:
    # For each non-root node v, there must be exactly 1 unit of flow arriving.
    # Root sends out n-1 units total.
    # Flow on arc (i->j) or (j->i) can only be nonzero if x[i,j]=1.

    # Directed flow variables for each undirected edge, both directions
    f = {}
    for (i, j) in edges:
        f[(i, j)] = model.addVar(lb=0, ub=n - 1, name=f"f_{i}_{j}")
        f[(j, i)] = model.addVar(lb=0, ub=n - 1, name=f"f_{j}_{i}")

    # Flow capacity: flow in either direction bounded by (n-1)*x
    for (i, j) in edges:
        model.addConstr(f[(i, j)] <= (n - 1) * x[(i, j)], name=f"cap_fwd_{i}_{j}")
        model.addConstr(f[(j, i)] <= (n - 1) * x[(i, j)], name=f"cap_bwd_{i}_{j}")

    # Flow conservation
    root = 1
    for node in range(1, n + 1):
        out_flow = gp.quicksum(f[(node, k)] for k in range(1, n + 1) if node != k and
                               ((min(node, k), max(node, k)) in set(edges)))
        in_flow = gp.quicksum(f[(k, node)] for k in range(1, n + 1) if node != k and
                              ((min(node, k), max(node, k)) in set(edges)))
        if node == root:
            # Root supplies n-1 units
            model.addConstr(out_flow - in_flow == n - 1, name=f"flow_root")
        else:
            # Every other node consumes exactly 1 unit
            model.addConstr(in_flow - out_flow == 1, name=f"flow_{node}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}