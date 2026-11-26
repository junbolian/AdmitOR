import gurobipy as gp
from gurobipy import GRB
from itertools import combinations

def solve(params):
    cost_1_2 = params["cost_1_2"]
    cost_1_3 = params["cost_1_3"]
    cost_1_4 = params["cost_1_4"]
    cost_1_5 = params["cost_1_5"]
    cost_2_3 = params["cost_2_3"]
    cost_2_4 = params["cost_2_4"]
    cost_2_5 = params["cost_2_5"]
    cost_3_4 = params["cost_3_4"]
    cost_3_5 = params["cost_3_5"]
    cost_4_5 = params["cost_4_5"]
    n = int(params["num_cities"])

    # Build cost dictionary for undirected edges (i < j), 1-indexed
    cost = {}
    cost[(1, 2)] = cost_1_2
    cost[(1, 3)] = cost_1_3
    cost[(1, 4)] = cost_1_4
    cost[(1, 5)] = cost_1_5
    cost[(2, 3)] = cost_2_3
    cost[(2, 4)] = cost_2_4
    cost[(2, 5)] = cost_2_5
    cost[(3, 4)] = cost_3_4
    cost[(3, 5)] = cost_3_5
    cost[(4, 5)] = cost_4_5

    cities = list(range(1, n + 1))
    edges = [(i, j) for i in cities for j in cities if i < j]

    model = gp.Model("TSP")
    model.setParam("OutputFlag", 0)

    # Binary variable for each edge: 1 if edge is in the tour
    x = model.addVars(edges, vtype=GRB.BINARY, name="x")

    # Objective: minimize total travel cost
    model.setObjective(
        gp.quicksum(cost[(i, j)] * x[(i, j)] for (i, j) in edges),
        GRB.MINIMIZE
    )

    # Degree constraints: each city has exactly 2 edges in the tour
    for city in cities:
        incident = [x[(i, j)] for (i, j) in edges if i == city or j == city]
        model.addConstr(gp.quicksum(incident) == 2, name=f"degree_{city}")

    # Subtour elimination via callback (lazy constraints)
    def subtour_elim(model_cb, where):
        if where == GRB.Callback.MIPSOL:
            x_vals = model_cb.cbGetSolution(x)
            # Build adjacency list from selected edges
            adj = {c: [] for c in cities}
            for (i, j) in edges:
                if x_vals[(i, j)] > 0.5:
                    adj[i].append(j)
                    adj[j].append(i)

            # Find connected components
            visited = set()
            components = []
            for start in cities:
                if start not in visited:
                    component = []
                    stack = [start]
                    while stack:
                        node = stack.pop()
                        if node not in visited:
                            visited.add(node)
                            component.append(node)
                            for nb in adj[node]:
                                if nb not in visited:
                                    stack.append(nb)
                    components.append(component)

            # If more than one component, add subtour elimination constraints
            if len(components) > 1:
                for comp in components:
                    if len(comp) < len(cities):
                        comp_set = set(comp)
                        sub_edges = [
                            x[(i, j)] for (i, j) in edges
                            if i in comp_set and j in comp_set
                        ]
                        model_cb.cbLazy(
                            gp.quicksum(sub_edges) <= len(comp) - 1
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