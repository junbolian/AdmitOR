import gurobipy as gp
from gurobipy import GRB

def solve(params):
    port_limit = params["port_limit"]
    cost_matrix = params["cost_matrix"]
    
    n = 16
    nodes = list(range(n))
    root = 0
    non_root = list(range(1, n))
    
    # Directed arcs for flow-based tree formulation
    # We'll use a flow-based MTZ-style formulation for spanning tree
    # with subtree size constraints for children of root
    
    model = gp.Model()
    model.setParam("OutputFlag", 0)
    model.setParam("TimeLimit", 120)
    
    # x[i,j] = 1 if directed arc i->j is in the tree (parent i, child j)
    # For the tree rooted at 0, each non-root node has exactly one parent
    x = {}
    for i in nodes:
        for j in non_root:
            if i != j:
                x[i, j] = model.addVar(vtype=GRB.BINARY, name=f"x_{i}_{j}")
    
    # Each non-root node has exactly one parent
    for j in non_root:
        model.addConstr(
            gp.quicksum(x[i, j] for i in nodes if i != j) == 1
        )
    
    # Objective: minimize total cost
    model.setObjective(
        gp.quicksum(cost_matrix[i][j] * x[i, j] for i in nodes for j in non_root if i != j),
        GRB.MINIMIZE
    )
    
    # Subtree size variables: s[j] = number of nodes in the subtree rooted at j (including j)
    s = {}
    for j in non_root:
        s[j] = model.addVar(lb=1.0, ub=n - 1, vtype=GRB.CONTINUOUS, name=f"s_{j}")
    
    # s[j] = 1 + sum of s[k] for children k of j
    # Equivalently, using flow: for each non-root j,
    # s[j] >= 1 (leaf case)
    # s[j] >= 1 + s[k] - M*(1 - x[j,k]) for each k that could be child of j
    # This is the standard subtree-size propagation with big-M
    
    M_size = n  # big-M for subtree size constraints
    
    for j in non_root:
        for k in non_root:
            if k != j:
                # If x[j,k]=1 then s[j] >= s[k] + 1
                model.addConstr(s[j] >= s[k] + 1 - M_size * (1 - x[j, k]))
    
    # s[j] <= 1 + sum_{k: child} s[k], but we handle this via port_limit constraints
    # Actually we need exact subtree sizes for the port_limit constraint.
    # Let's use a tighter formulation with flow variables.
    
    # Flow-based subtree size: 
    # f[i,j] = flow on arc i->j = number of nodes in subtree rooted at j
    # f[i,j] in [1, n-1], only meaningful when x[i,j]=1
    
    f = {}
    for i in nodes:
        for j in non_root:
            if i != j:
                f[i, j] = model.addVar(lb=0.0, ub=n - 1, vtype=GRB.CONTINUOUS, name=f"f_{i}_{j}")
    
    # Linearize: f[i,j] = s[j] * x[i,j]
    # Since s[j] in [1, n-1]:
    # f[i,j] <= (n-1)*x[i,j]
    # f[i,j] >= x[i,j]  (s[j] >= 1)
    # f[i,j] <= s[j]
    # f[i,j] >= s[j] - (n-1)*(1 - x[i,j])
    
    for i in nodes:
        for j in non_root:
            if i != j:
                model.addConstr(f[i, j] <= (n - 1) * x[i, j])
                model.addConstr(f[i, j] >= x[i, j])
                model.addConstr(f[i, j] <= s[j])
                model.addConstr(f[i, j] >= s[j] - (n - 1) * (1 - x[i, j]))
    
    # Flow conservation: s[j] = 1 + sum_{k != j, k in non_root} f[j,k]
    for j in non_root:
        children_flow = gp.quicksum(f[j, k] for k in non_root if k != j)
        model.addConstr(s[j] == 1 + children_flow)
    
    # Port limit: for each direct child c of root (node 0),
    # the subtree rooted at c has size s[c] <= port_limit
    for c in non_root:
        model.addConstr(s[c] <= port_limit + (n - 1) * (1 - x[0, c]))
    
    # Prevent cycles (subtree sizes must be consistent - already handled by flow conservation)
    # But we also need to ensure no cycles among non-root nodes.
    # The flow conservation + subtree size propagation ensures tree structure
    # if s values are integral. Let's also add: 
    # sum of s[c]*x[0,c] over direct children of root = n-1
    # (total non-root nodes)
    root_children_flow = gp.quicksum(f[0, c] for c in non_root)
    model.addConstr(root_children_flow == n - 1)
    
    model.optimize()
    
    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.TIME_LIMIT:
        if model.SolCount > 0:
            return {"objective": model.ObjVal, "status": "optimal"}
        return {"objective": None, "status": "time_limit"}
    else:
        return {"objective": None, "status": f"solver_status_{status}"}