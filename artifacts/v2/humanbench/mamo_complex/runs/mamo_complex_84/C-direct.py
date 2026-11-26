import gurobipy as gp
from gurobipy import GRB
from itertools import combinations

def solve(params):
    cost_12 = params["cost_12"]
    cost_13 = params["cost_13"]
    cost_14 = params["cost_14"]
    cost_15 = params["cost_15"]
    cost_16 = params["cost_16"]
    cost_23 = params["cost_23"]
    cost_24 = params["cost_24"]
    cost_25 = params["cost_25"]
    cost_26 = params["cost_26"]
    cost_34 = params["cost_34"]
    cost_35 = params["cost_35"]
    cost_36 = params["cost_36"]
    cost_45 = params["cost_45"]
    cost_46 = params["cost_46"]
    cost_56 = params["cost_56"]
    n = params["n_cities"]

    # Build symmetric cost dict (1-indexed)
    cost = {}
    cost[(1,2)] = cost[(2,1)] = cost_12
    cost[(1,3)] = cost[(3,1)] = cost_13
    cost[(1,4)] = cost[(4,1)] = cost_14
    cost[(1,5)] = cost[(5,1)] = cost_15
    cost[(1,6)] = cost[(6,1)] = cost_16
    cost[(2,3)] = cost[(3,2)] = cost_23
    cost[(2,4)] = cost[(4,2)] = cost_24
    cost[(2,5)] = cost[(5,2)] = cost_25
    cost[(2,6)] = cost[(6,2)] = cost_26
    cost[(3,4)] = cost[(4,3)] = cost_34
    cost[(3,5)] = cost[(5,3)] = cost_35
    cost[(3,6)] = cost[(6,3)] = cost_36
    cost[(4,5)] = cost[(5,4)] = cost_45
    cost[(4,6)] = cost[(6,4)] = cost_46
    cost[(5,6)] = cost[(6,5)] = cost_56

    cities = list(range(1, n + 1))
    edges = [(i, j) for i in cities for j in cities if i < j]

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Binary variable for each edge
    x = model.addVars(edges, vtype=GRB.BINARY, name="x")

    # Objective: minimize total cost
    model.setObjective(
        gp.quicksum(cost[(i, j)] * x[i, j] for (i, j) in edges),
        GRB.MINIMIZE
    )

    # Degree constraints: each city has exactly 2 edges
    for city in cities:
        model.addConstr(
            gp.quicksum(x[i, j] for (i, j) in edges if i == city or j == city) == 2,
            name=f"degree_{city}"
        )

    # Subtour elimination via lazy constraints (callback)
    model._x = x
    model._edges = edges
    model._cities = cities

    def subtour_callback(cb_model, where):
        if where == GRB.Callback.MIPSOL:
            x_vals = cb_model.cbGetSolution(cb_model._x)
            # Build adjacency
            selected = [(i, j) for (i, j) in cb_model._edges if x_vals[i, j] > 0.5]
            # Find connected components
            adj = {c: [] for c in cb_model._cities}
            for (i, j) in selected:
                adj[i].append(j)
                adj[j].append(i)
            visited = set()
            components = []
            for c in cb_model._cities:
                if c not in visited:
                    comp = []
                    stack = [c]
                    while stack:
                        node = stack.pop()
                        if node not in visited:
                            visited.add(node)
                            comp.append(node)
                            stack.extend(adj[node])
                    components.append(comp)
            # Add subtour elimination for any component that doesn't include all cities
            for comp in components:
                if len(comp) < len(cb_model._cities):
                    comp_edges = [(i, j) for (i, j) in cb_model._edges
                                  if i in comp and j in comp]
                    cb_model.cbLazy(
                        gp.quicksum(cb_model._x[i, j] for (i, j) in comp_edges)
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