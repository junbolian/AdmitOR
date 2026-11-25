import gurobipy as gp
from gurobipy import GRB

def solve(params):
    cost_matrix = params["pipe_cost_matrix"]
    max_degree = params["max_degree_per_node"]
    
    n = 12
    nodes = list(range(n))
    # Edges as undirected pairs (i < j)
    edges = [(i, j) for i in range(n) for j in range(i+1, n)]
    
    model = gp.Model("min_cost_spanning_tree")
    model.setParam("OutputFlag", 0)
    
    # Binary variable: x[i,j] = 1 if edge (i,j) is in the tree
    x = model.addVars(edges, vtype=GRB.BINARY, name="x")
    
    # Objective: minimize total cost
    model.setObjective(
        gp.quicksum(cost_matrix[i][j] * x[i, j] for i, j in edges),
        GRB.MINIMIZE
    )
    
    # A spanning tree on n nodes has exactly n-1 edges
    model.addConstr(gp.quicksum(x[i, j] for i, j in edges) == n - 1, name="tree_edges")
    
    # Degree constraint: each node can have at most max_degree connections
    for node in nodes:
        incident = [(i, j) for (i, j) in edges if i == node or j == node]
        model.addConstr(
            gp.quicksum(x[i, j] for i, j in incident) <= max_degree,
            name=f"degree_{node}"
        )
    
    # Subtour elimination via Miller-Tucker-Zemlin (MTZ) formulation
    # We treat the tree as a directed graph rooted at node 0.
    # For each undirected edge (i,j), introduce directed variables y[i,j] and y[j,i].
    # Exactly one direction is used if the edge is selected.
    # MTZ ordering variables u[i] for i > 0
    
    directed_edges = [(i, j) for i in range(n) for j in range(n) if i != j]
    
    y = model.addVars(directed_edges, vtype=GRB.BINARY, name="y")
    u = model.addVars(nodes, vtype=GRB.CONTINUOUS, lb=0, ub=n-1, name="u")
    
    # Link directed and undirected: y[i,j] + y[j,i] == x[i,j]
    for (i, j) in edges:
        model.addConstr(y[i, j] + y[j, i] == x[i, j], name=f"link_{i}_{j}")
    
    # Flow conservation for spanning tree rooted at node 0:
    # Each non-root node has exactly one incoming arc (its parent in the tree)
    for node in range(1, n):
        in_arcs = [(i, node) for i in nodes if i != node]
        model.addConstr(
            gp.quicksum(y[i, node] for i, v in in_arcs) == 1,
            name=f"one_parent_{node}"
        )
    
    # Root has no incoming arc
    model.addConstr(
        gp.quicksum(y[i, 0] for i in range(1, n)) == 0,
        name="root_no_parent"
    )
    
    # MTZ subtour elimination: u[i] - u[j] + n * y[i,j] <= n - 1 for i,j != root
    for (i, j) in directed_edges:
        if i != 0 and j != 0:
            model.addConstr(
                u[i] - u[j] + n * y[i, j] <= n - 1,
                name=f"mtz_{i}_{j}"
            )
    
    # Fix root ordering label
    model.addConstr(u[0] == 0, name="root_label")
    
    model.optimize()
    
    if model.Status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.TIME_LIMIT:
        return {"objective": None, "status": "time_limit"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}