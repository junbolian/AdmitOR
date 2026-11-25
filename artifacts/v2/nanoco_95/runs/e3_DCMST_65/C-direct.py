import gurobipy as gp
from gurobipy import GRB

def solve(params):
    cost_matrix = params["cost_matrix"]
    max_degree = params["max_degree"]
    num_nodes = params["num_nodes"]

    n = num_nodes  # 15, structural constant for index setup

    # Build cost dict (0-indexed)
    c = {}
    for i in range(n):
        for j in range(n):
            c[i, j] = cost_matrix[i * n + j]

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # x[i,j] = 1 if undirected edge (i,j) selected, only for i < j
    x = {}
    for i in range(n):
        for j in range(i + 1, n):
            x[i, j] = model.addVar(vtype=GRB.BINARY, name=f"x_{i}_{j}")

    # Objective: minimize total cost
    model.setObjective(
        gp.quicksum((c[i, j] + c[j, i]) / 2 * x[i, j] for i in range(n) for j in range(i + 1, n)),
        GRB.MINIMIZE
    )

    # A spanning tree has exactly n-1 edges
    model.addConstr(
        gp.quicksum(x[i, j] for i in range(n) for j in range(i + 1, n)) == n - 1,
        name="tree_size"
    )

    # Degree constraints: each node has at most max_degree edges
    for i in range(n):
        edges_i = []
        for j in range(n):
            if j != i:
                ei = (min(i, j), max(i, j))
                edges_i.append(x[ei[0], ei[1]])
        model.addConstr(gp.quicksum(edges_i) <= max_degree, name=f"deg_{i}")

    # Subtour elimination via Miller-Tucker-Zemlin (MTZ) formulation
    # We need a rooted spanning tree structure.
    # Use node 0 as root. For each non-root node j, there is exactly one parent.
    # u[i] = ordering label for node i (root = 0, others in [1, n-1])
    # For each directed arc (i->j) that is "used" (i is parent of j), enforce u[i] - u[j] + n*y[i,j] <= n-1

    # y[i,j] = 1 means i is the parent of j in the rooted tree (directed arc i->j)
    y = {}
    for i in range(n):
        for j in range(n):
            if i != j:
                y[i, j] = model.addVar(vtype=GRB.BINARY, name=f"y_{i}_{j}")

    u = model.addVars(n, lb=0.0, ub=n - 1, vtype=GRB.CONTINUOUS, name="u")

    # Root label
    model.addConstr(u[0] == 0, name="root_label")

    # Each non-root node has exactly one parent
    for j in range(1, n):
        model.addConstr(
            gp.quicksum(y[i, j] for i in range(n) if i != j) == 1,
            name=f"one_parent_{j}"
        )

    # Root has no parent
    model.addConstr(
        gp.quicksum(y[i, 0] for i in range(1, n)) == 0,
        name="root_no_parent"
    )

    # Link y to x: if y[i,j]=1 then x[min,max]=1
    for i in range(n):
        for j in range(n):
            if i != j:
                ei = (min(i, j), max(i, j))
                model.addConstr(y[i, j] <= x[ei[0], ei[1]], name=f"link_yx_{i}_{j}")

    # Each undirected edge used must have exactly one direction as parent->child
    for i in range(n):
        for j in range(i + 1, n):
            model.addConstr(y[i, j] + y[j, i] == x[i, j], name=f"dir_{i}_{j}")

    # MTZ subtour elimination
    for i in range(n):
        for j in range(1, n):
            if i != j:
                model.addConstr(
                    u[i] - u[j] + n * y[i, j] <= n - 1,
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