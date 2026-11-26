import gurobipy as gp
from gurobipy import GRB
from itertools import combinations

def solve(params):
    n = params["num_customers"]
    d = params["distance_matrix"]  # d[i][j] or d[(i,j)], we'll handle both

    # Normalize distance matrix to a dict keyed by (i,j) with 0-based or 1-based indices
    # We'll use 0-based internally: nodes 0..n-1
    # d may be a list of lists or a dict; handle both
    def dist(i, j):
        if isinstance(d, dict):
            if (i, j) in d:
                return d[(i, j)]
            elif (j, i) in d:
                return d[(j, i)]
            else:
                return 0.0
        else:
            # list of lists
            return d[i][j]

    nodes = list(range(n))

    model = gp.Model("TSP")
    model.setParam("OutputFlag", 0)

    # Decision variables: x[i,j] = 1 if edge (i,j) is used, for i != j
    x = {}
    for i in nodes:
        for j in nodes:
            if i != j:
                x[i, j] = model.addVar(vtype=GRB.BINARY, name=f"x_{i}_{j}")

    model.update()

    # Objective: minimize total distance
    model.setObjective(
        gp.quicksum(dist(i, j) * x[i, j] for i in nodes for j in nodes if i != j),
        GRB.MINIMIZE
    )

    # Each node must be entered exactly once
    for j in nodes:
        model.addConstr(
            gp.quicksum(x[i, j] for i in nodes if i != j) == 1,
            name=f"enter_{j}"
        )

    # Each node must be left exactly once
    for i in nodes:
        model.addConstr(
            gp.quicksum(x[i, j] for j in nodes if i != j) == 1,
            name=f"leave_{i}"
        )

    # Subtour elimination via callback (lazy constraints)
    # We use the standard MTZ or subtour callback approach.
    # Using a callback with lazy constraints for subtour elimination.

    model.setParam("LazyConstraints", 1)

    def subtour_elim(model, where):
        if where == GRB.Callback.MIPSOL:
            x_val = model.cbGetSolution(
                [x[i, j] for i in nodes for j in nodes if i != j]
            )
            x_sol = {}
            idx = 0
            for i in nodes:
                for j in nodes:
                    if i != j:
                        x_sol[i, j] = x_val[idx]
                        idx += 1

            # Find subtours
            unvisited = set(nodes)
            cycles = []
            while unvisited:
                cycle = []
                current = next(iter(unvisited))
                while True:
                    cycle.append(current)
                    unvisited.discard(current)
                    # Find next node
                    next_node = None
                    for j in nodes:
                        if j != current and x_sol.get((current, j), 0) > 0.5:
                            next_node = j
                            break
                    if next_node is None or next_node in cycle:
                        break
                    current = next_node
                cycles.append(cycle)

            # Add subtour elimination constraints for cycles that don't include all nodes
            for cycle in cycles:
                if len(cycle) < n:
                    model.cbLazy(
                        gp.quicksum(x[i, j] for i in cycle for j in cycle if i != j)
                        <= len(cycle) - 1
                    )

    model.optimize(subtour_elim)

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.TIME_LIMIT:
        return {"objective": None, "status": "time_limit"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}