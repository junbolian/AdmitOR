import gurobipy as gp
from gurobipy import GRB
from itertools import combinations

def solve(params):
    c12 = params["c12"]
    c13 = params["c13"]
    c14 = params["c14"]
    c15 = params["c15"]
    c16 = params["c16"]
    c23 = params["c23"]
    c24 = params["c24"]
    c25 = params["c25"]
    c26 = params["c26"]
    c34 = params["c34"]
    c35 = params["c35"]
    c36 = params["c36"]
    c45 = params["c45"]
    c46 = params["c46"]
    c56 = params["c56"]

    n = 6
    cities = list(range(1, n + 1))

    # Build symmetric cost dict for edges (i,j) with i < j
    cost = {
        (1, 2): c12, (1, 3): c13, (1, 4): c14, (1, 5): c15, (1, 6): c16,
        (2, 3): c23, (2, 4): c24, (2, 5): c25, (2, 6): c26,
        (3, 4): c34, (3, 5): c35, (3, 6): c36,
        (4, 5): c45, (4, 6): c46,
        (5, 6): c56,
    }

    edges = list(cost.keys())

    model = gp.Model("TSP")
    model.setParam("OutputFlag", 0)

    # Binary variable for each edge
    x = model.addVars(edges, vtype=GRB.BINARY, name="x")

    # Objective: minimize total travel cost
    model.setObjective(
        gp.quicksum(cost[e] * x[e] for e in edges),
        GRB.MINIMIZE
    )

    # Degree constraints: each city must have exactly 2 edges selected
    for city in cities:
        incident = [e for e in edges if city in e]
        model.addConstr(gp.quicksum(x[e] for e in incident) == 2, name=f"degree_{city}")

    # Subtour elimination via lazy constraints callback
    def subtour_elim(model, where):
        if where == GRB.Callback.MIPSOL:
            x_vals = model.cbGetSolution(x)
            # Build adjacency list
            selected = [e for e in edges if x_vals[e] > 0.5]
            adj = {c: [] for c in cities}
            for i, j in selected:
                adj[i].append(j)
                adj[j].append(i)

            # Find connected components via BFS
            visited = set()
            components = []
            for start in cities:
                if start not in visited:
                    component = []
                    queue = [start]
                    while queue:
                        node = queue.pop()
                        if node in visited:
                            continue
                        visited.add(node)
                        component.append(node)
                        for nb in adj[node]:
                            if nb not in visited:
                                queue.append(nb)
                    components.append(component)

            # If more than one component, add subtour elimination constraints
            if len(components) > 1:
                for comp in components:
                    if len(comp) < n:
                        sub_edges = [
                            e for e in edges
                            if e[0] in comp and e[1] in comp
                        ]
                        model.cbLazy(
                            gp.quicksum(x[e] for e in sub_edges) <= len(comp) - 1
                        )

    model.setParam("LazyConstraints", 1)
    model.optimize(subtour_elim)

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.TIME_LIMIT:
        return {"objective": None, "status": "time_limit"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}