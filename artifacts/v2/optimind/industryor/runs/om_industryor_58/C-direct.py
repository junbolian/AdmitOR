import gurobipy as gp
from gurobipy import GRB
from itertools import combinations

def solve(params):
    N = params["N"]
    distance_matrix_upper = params["distance_matrix"]

    # Build full distance dict from upper-triangular entries (row-major for i<j)
    dist = {}
    idx = 0
    for i in range(N):
        for j in range(i + 1, N):
            dist[i, j] = distance_matrix_upper[idx]
            dist[j, i] = distance_matrix_upper[idx]
            idx += 1

    nodes = list(range(N))

    model = gp.Model("TSP")
    model.setParam("OutputFlag", 0)

    # Binary variables: x[i,j] = 1 if edge (i,j) is used, for i < j
    x = {}
    for i in range(N):
        for j in range(i + 1, N):
            x[i, j] = model.addVar(vtype=GRB.BINARY, name=f"x_{i}_{j}")

    # Objective: minimize total distance
    model.setObjective(
        gp.quicksum(dist[i, j] * x[i, j] for i in range(N) for j in range(i + 1, N)),
        GRB.MINIMIZE
    )

    # Degree constraints: each node has exactly 2 edges
    for k in nodes:
        edges_k = []
        for i in range(N):
            for j in range(i + 1, N):
                if i == k or j == k:
                    edges_k.append(x[i, j])
        model.addConstr(gp.quicksum(edges_k) == 2, name=f"degree_{k}")

    # Subtour elimination via lazy constraints (callback)
    model._x = x
    model._N = N

    def subtour_elim(model, where):
        if where == GRB.Callback.MIPSOL:
            x_val = {}
            for i in range(model._N):
                for j in range(i + 1, model._N):
                    x_val[i, j] = model.cbGetSolution(model._x[i, j])
                    x_val[j, i] = x_val[i, j]

            # Find connected components (subtours)
            visited = [False] * model._N
            components = []
            for start in range(model._N):
                if not visited[start]:
                    component = []
                    stack = [start]
                    while stack:
                        node = stack.pop()
                        if visited[node]:
                            continue
                        visited[node] = True
                        component.append(node)
                        for neighbor in range(model._N):
                            if neighbor != node and not visited[neighbor]:
                                if x_val.get((node, neighbor), 0) > 0.5:
                                    stack.append(neighbor)
                    components.append(component)

            # Add subtour elimination cuts for any subtour not spanning all nodes
            for comp in components:
                if len(comp) < model._N:
                    # Sum of edges within this subset must be <= |subset| - 1
                    subset_edges = []
                    for i in comp:
                        for j in comp:
                            if i < j:
                                subset_edges.append(model._x[i, j])
                    model.cbLazy(
                        gp.quicksum(subset_edges) <= len(comp) - 1
                    )

    model.setParam("LazyConstraints", 1)
    model.optimize(subtour_elim)

    if model.Status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.TIME_LIMIT:
        return {"objective": None, "status": "time_limit"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}