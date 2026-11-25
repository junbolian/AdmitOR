import gurobipy as gp
from gurobipy import GRB

def solve(params):
    cost_matrix = params["cost_matrix"]
    n = 10
    nodes = list(range(n))

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # x[i,j] = 1 if truck travels from i to j
    x = {}
    for i in nodes:
        for j in nodes:
            if i != j:
                x[i, j] = model.addVar(vtype=GRB.BINARY, name=f"x_{i}_{j}")

    # u[i] = position of node i in tour (MTZ subtour elimination), for i in 1..9
    u = {}
    for i in range(1, n):
        u[i] = model.addVar(lb=1, ub=n - 1, vtype=GRB.CONTINUOUS, name=f"u_{i}")

    # Objective
    model.setObjective(
        gp.quicksum(cost_matrix[i][j] * x[i, j] for i in nodes for j in nodes if i != j),
        GRB.MINIMIZE
    )

    # Each node is departed exactly once
    for i in nodes:
        model.addConstr(gp.quicksum(x[i, j] for j in nodes if j != i) == 1, name=f"out_{i}")

    # Each node is arrived at exactly once
    for j in nodes:
        model.addConstr(gp.quicksum(x[i, j] for i in nodes if i != j) == 1, name=f"in_{j}")

    # MTZ subtour elimination constraints
    for i in range(1, n):
        for j in range(1, n):
            if i != j:
                model.addConstr(
                    u[i] - u[j] + (n - 1) * x[i, j] <= n - 2,
                    name=f"mtz_{i}_{j}"
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