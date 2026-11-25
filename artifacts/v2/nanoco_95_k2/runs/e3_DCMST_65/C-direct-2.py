import gurobipy as gp
from gurobipy import GRB

def solve(params):
    cost_matrix = params["cost_matrix"]
    max_degree = params["max_degree"]
    
    n = 15
    nodes = list(range(n))
    
    # Edges: upper triangle only (undirected)
    edges = [(i, j) for i in range(n) for j in range(i+1, n)]
    
    model = gp.Model("min_cost_spanning_tree")
    model.setParam("OutputFlag", 0)
    
    # Binary variable: x[i,j] = 1 if edge (i,j) is in the tree
    x = model.addVars(edges, vtype=GRB.BINARY, name="x")
    
    # Objective: minimize total construction cost
    model.setObjective(
        gp.quicksum(cost_matrix[i][j] * x[i, j] for i, j in edges),
        GRB.MINIMIZE
    )
    
    # A spanning tree on n nodes has exactly n-1 edges
    model.addConstr(gp.quicksum(x[i, j] for i, j in edges) == n - 1, name="tree_size")
    
    # Degree constraint: each node has at most max_degree connections
    for k in nodes:
        incident = [(i, j) for (i, j) in edges if i == k or j == k]
        model.addConstr(
            gp.quicksum(x[i, j] for i, j in incident) <= max_degree,
            name=f"degree_{k}"
        )
    
    # Subtour elimination via Miller-Tucker-Zemlin (MTZ) formulation
    # We orient edges for MTZ: use directed variables u[i] as ordering labels
    # Root at node 0; for each directed arc, enforce order to prevent cycles
    
    # Directed edge variables for MTZ
    arcs = [(i, j) for i in nodes for j in nodes if i != j]
    y = model.addVars(arcs, vtype=GRB.BINARY, name="y")
    
    # Link undirected x to directed y: x[i,j] = y[i,j] + y[j,i]
    for (i, j) in edges:
        model.addConstr(x[i, j] == y[i, j] + y[j, i], name=f"link_{i}_{j}")
    
    # MTZ order variables: u[i] in [1, n-1] for i != 0
    u = model.addVars(nodes, lb=0.0, ub=n - 1, vtype=GRB.CONTINUOUS, name="u")
    model.addConstr(u[0] == 0, name="root_order")
    
    # MTZ subtour elimination: if arc (i->j) is used, u[j] >= u[i] + 1
    big_M = n
    for (i, j) in arcs:
        if j != 0:  # root has u=0, don't constrain arcs into root via MTZ
            model.addConstr(
                u[j] >= u[i] + 1 - big_M * (1 - y[i, j]),
                name=f"mtz_{i}_{j}"
            )
    
    # Each non-root node must have exactly one incoming arc (tree structure)
    for j in nodes:
        if j != 0:
            incoming = [(i, j) for i in nodes if i != j]
            model.addConstr(
                gp.quicksum(y[i, j] for i, j in incoming) == 1,
                name=f"one_parent_{j}"
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