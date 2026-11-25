import gurobipy as gp
from gurobipy import GRB

def solve(params):
    cost_matrix = params["pipe_cost_matrix"]
    max_degree = params["max_degree_per_node"]
    
    n = 12  # number of nodes
    nodes = list(range(n))
    # edges as (i,j) with i < j
    edges = [(i, j) for i in nodes for j in nodes if i < j]
    
    model = gp.Model("district_cooling_mst")
    model.setParam("OutputFlag", 0)
    
    # Binary variable: x[i,j] = 1 if edge (i,j) is in the spanning tree
    x = model.addVars(edges, vtype=GRB.BINARY, name="x")
    
    # Objective: minimize total installation cost
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
    # We root the tree at node 0 and use ordering variables u[i] for i in 1..n-1
    # For each directed arc (i->j) in the tree, u[j] = u[i] + 1
    # We need directed edge variables to apply MTZ
    
    # Directed edge variables for MTZ
    dir_edges = [(i, j) for i in nodes for j in nodes if i != j]
    y = model.addVars(dir_edges, vtype=GRB.BINARY, name="y")
    
    # u[i]: ordering variable (position in tree from root)
    u = model.addVars(nodes, lb=0.0, ub=n - 1.0, vtype=GRB.CONTINUOUS, name="u")
    
    # Root node u[0] = 0
    model.addConstr(u[0] == 0, name="root")
    
    # Relationship between undirected x and directed y:
    # x[i,j] = y[i,j] + y[j,i] for i < j
    for i, j in edges:
        model.addConstr(x[i, j] == y[i, j] + y[j, i], name=f"dir_link_{i}_{j}")
    
    # Each non-root node has exactly one parent (in-degree = 1 in directed tree)
    for k in nodes:
        if k == 0:
            # Root has in-degree 0
            model.addConstr(
                gp.quicksum(y[i, k] for i in nodes if i != k) == 0,
                name=f"root_indegree"
            )
        else:
            model.addConstr(
                gp.quicksum(y[i, k] for i in nodes if i != k) == 1,
                name=f"indegree_{k}"
            )
    
    # MTZ subtour elimination: if y[i,j]=1 then u[j] >= u[i] + 1
    big_M = n - 1
    for i, j in dir_edges:
        if j != 0:  # skip arcs into root
            model.addConstr(
                u[j] >= u[i] + 1 - big_M * (1 - y[i, j]),
                name=f"mtz_{i}_{j}"
            )
    
    model.optimize()
    
    if model.Status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.TIME_LIMIT:
        return {"objective": None, "status": "time_limit"}
    else:
        return {"objective": None, "status": f"solver_status_{model.Status}"}