import gurobipy as gp
from gurobipy import GRB

def solve(params):
    costs = params["costs"]
    max_degree = params["max_degree"]
    
    n = 12
    nodes = list(range(n))
    # Edges as undirected pairs (i < j)
    edges = [(i, j) for i in range(n) for j in range(i+1, n)]
    
    model = gp.Model()
    model.setParam("OutputFlag", 0)
    
    # Binary variable: x[i,j] = 1 if edge (i,j) is in the spanning tree
    x = model.addVars(edges, vtype=GRB.BINARY, name="x")
    
    # Objective: minimize total cost
    model.setObjective(
        gp.quicksum(costs[i][j] * x[i, j] for i, j in edges),
        GRB.MINIMIZE
    )
    
    # A spanning tree on n nodes has exactly n-1 edges
    model.addConstr(gp.quicksum(x[i, j] for i, j in edges) == n - 1, name="tree_size")
    
    # Degree constraint: each node has at most max_degree connections
    for i in nodes:
        neighbors = (
            gp.quicksum(x[i, j] for j in range(i+1, n)) +
            gp.quicksum(x[j, i] for j in range(0, i))
        )
        model.addConstr(neighbors <= max_degree, name=f"deg_{i}")
    
    # Subtour elimination via Miller-Tucker-Zemlin (MTZ) formulation
    # Use directed auxiliary variables for MTZ on undirected edges
    # For each undirected edge, create two directed arcs
    arcs = [(i, j) for i in nodes for j in nodes if i != j]
    
    # y[i,j] = 1 if arc i->j is used (directed version of x for MTZ)
    y = model.addVars(arcs, vtype=GRB.BINARY, name="y")
    
    # u[i] = ordering label for MTZ (root node 0 has u=0)
    u = model.addVars(nodes, lb=0.0, ub=n-1, vtype=GRB.CONTINUOUS, name="u")
    
    # Link y to x: for each undirected edge (i,j), exactly one direction is used if edge is selected
    for i, j in edges:
        model.addConstr(y[i, j] + y[j, i] == x[i, j], name=f"dir_{i}_{j}")
    
    # Fix root
    model.addConstr(u[0] == 0, name="root")
    
    # MTZ subtour elimination: if arc i->j is used, u[j] >= u[i] + 1
    BIG_M = n
    for i, j in arcs:
        if j != 0:  # root has no incoming arcs in rooted tree
            model.addConstr(
                u[j] >= u[i] + 1 - BIG_M * (1 - y[i, j]),
                name=f"mtz_{i}_{j}"
            )
    
    # Each non-root node has exactly one incoming arc (tree property)
    for j in nodes:
        if j != 0:
            model.addConstr(
                gp.quicksum(y[i, j] for i in nodes if i != j) == 1,
                name=f"in_{j}"
            )
    # Root has no incoming arc
    model.addConstr(
        gp.quicksum(y[i, 0] for i in nodes if i != 0) == 0,
        name="root_no_in"
    )
    
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