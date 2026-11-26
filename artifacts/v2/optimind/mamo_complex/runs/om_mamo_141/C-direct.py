def solve(params):
    import gurobipy as gp
    from gurobipy import GRB

    nodes = ['A', 'B', 'C', 'D', 'E', 'F']
    n = len(nodes)
    idx = {node: i for i, node in enumerate(nodes)}

    cost = {}
    for i in nodes:
        for j in nodes:
            if i != j:
                key = f"cost_{i}{j}"
                cost[i, j] = params[key]

    model = gp.Model("TSP")
    model.setParam("OutputFlag", 0)

    x = model.addVars(nodes, nodes, vtype=GRB.BINARY, name="x")

    # No self-loops
    for i in nodes:
        model.addConstr(x[i, i] == 0)

    # Each node is left exactly once
    for i in nodes:
        model.addConstr(gp.quicksum(x[i, j] for j in nodes if j != i) == 1)

    # Each node is entered exactly once
    for j in nodes:
        model.addConstr(gp.quicksum(x[i, j] for i in nodes if i != j) == 1)

    # MTZ subtour elimination
    u = model.addVars(nodes, lb=0, ub=n - 1, vtype=GRB.CONTINUOUS, name="u")
    for i in nodes:
        for j in nodes:
            if i != j and i != 'A' and j != 'A':
                model.addConstr(u[i] - u[j] + n * x[i, j] <= n - 1)

    model.setObjective(
        gp.quicksum(cost[i, j] * x[i, j] for i in nodes for j in nodes if i != j),
        GRB.MINIMIZE
    )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}