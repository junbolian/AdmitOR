import gurobipy as gp
from gurobipy import GRB

def solve(params):
    cost_matrix = params["cost_matrix"]
    n = params["num_checkpoints"]

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # x[i,j] = 1 if patrol goes from checkpoint i to checkpoint j
    x = {}
    for i in range(n):
        for j in range(n):
            if i != j:
                x[i, j] = model.addVar(vtype=GRB.BINARY, name=f"x_{i}_{j}")

    # u[i] = position of checkpoint i in the tour (MTZ subtour elimination)
    u = {}
    for i in range(1, n):
        u[i] = model.addVar(lb=1, ub=n - 1, vtype=GRB.CONTINUOUS, name=f"u_{i}")

    # Objective: minimize total transition cost
    model.setObjective(
        gp.quicksum(cost_matrix[i][j] * x[i, j] for i in range(n) for j in range(n) if i != j),
        GRB.MINIMIZE
    )

    # Each checkpoint is arrived at exactly once
    for j in range(n):
        model.addConstr(gp.quicksum(x[i, j] for i in range(n) if i != j) == 1)

    # Each checkpoint is departed from exactly once
    for i in range(n):
        model.addConstr(gp.quicksum(x[i, j] for j in range(n) if i != j) == 1)

    # MTZ subtour elimination constraints
    for i in range(1, n):
        for j in range(1, n):
            if i != j:
                model.addConstr(u[i] - u[j] + (n - 1) * x[i, j] <= n - 2)

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}