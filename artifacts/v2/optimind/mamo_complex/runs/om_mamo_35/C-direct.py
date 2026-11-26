import gurobipy as gp
from gurobipy import GRB
from itertools import combinations

def solve(params):
    n = 6
    cities = list(range(1, n + 1))

    # Build cost matrix from params (symmetric)
    cost = {}
    for i in cities:
        for j in cities:
            if i < j:
                cost[i, j] = params[f"cost_{i}_{j}"]
                cost[j, i] = params[f"cost_{i}_{j}"]
            elif i == j:
                cost[i, j] = 0.0

    model = gp.Model("TSP")
    model.setParam("OutputFlag", 0)

    # Decision variables: x[i,j] = 1 if edge (i,j) is used, for i < j
    edges = [(i, j) for i in cities for j in cities if i < j]
    x = model.addVars(edges, vtype=GRB.BINARY, name="x")

    # Objective: minimize total travel cost
    model.setObjective(
        gp.quicksum(cost[i, j] * x[i, j] for i, j in edges),
        GRB.MINIMIZE
    )

    # Degree constraints: each city must have exactly 2 edges
    for i in cities:
        model.addConstr(
            gp.quicksum(x[i, j] for j in cities if j > i) +
            gp.quicksum(x[j, i] for j in cities if j < i) == 2,
            name=f"degree_{i}"
        )

    # Subtour elimination via lazy constraints (SEC)
    model._x = x
    model._cities = cities

    def subtour_callback(model_cb, where):
        if where == GRB.Callback.MIPSOL:
            x_vals = model_cb.cbGetSolution(model_cb._x)
            # Build adjacency
            adj = {i: [] for i in model_cb._cities}
            for (i, j) in model_cb._x:
                if x_vals[i, j] > 0.5:
                    adj[i].append(j)
                    adj[j].append(i)
            # Find connected components
            visited = set()
            components = []
            for start in model_cb._cities:
                if start not in visited:
                    comp = []
                    stack = [start]
                    while stack:
                        node = stack.pop()
                        if node not in visited:
                            visited.add(node)
                            comp.append(node)
                            stack.extend(adj[node])
                    components.append(comp)
            # Add subtour elimination cuts for any component that doesn't include all cities
            for comp in components:
                if len(comp) < len(model_cb._cities):
                    comp_set = set(comp)
                    sub_edges = [
                        (i, j) for (i, j) in model_cb._x
                        if i in comp_set and j in comp_set
                    ]
                    model_cb.cbLazy(
                        gp.quicksum(model_cb._x[i, j] for (i, j) in sub_edges)
                        <= len(comp) - 1
                    )

    model.setParam("LazyConstraints", 1)
    model.optimize(subtour_callback)

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}