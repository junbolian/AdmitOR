import gurobipy as gp
from gurobipy import GRB

def solve(params):
    cost = params["cost"]
    n = 7  # number of cities
    cities = range(n)

    model = gp.Model("TSP_7cities")
    model.setParam("OutputFlag", 0)

    # Binary decision variables: x[i][j] = 1 if we travel from city i to city j
    x = {}
    for i in cities:
        for j in cities:
            if i != j:
                x[i, j] = model.addVar(vtype=GRB.BINARY, name=f"x_{i}_{j}")

    # Position variables for MTZ subtour elimination
    # u[i] = position of city i in the tour (City 0 fixed at 0)
    u = {}
    for i in cities:
        if i == 0:
            u[i] = model.addVar(lb=0, ub=0, vtype=GRB.INTEGER, name=f"u_{i}")
        else:
            u[i] = model.addVar(lb=1, ub=n - 1, vtype=GRB.INTEGER, name=f"u_{i}")

    model.update()

    # Objective: minimize total delivery cost
    model.setObjective(
        gp.quicksum(cost[i][j] * x[i, j] for i in cities for j in cities if i != j),
        GRB.MINIMIZE
    )

    # Each city has exactly one outgoing arc
    for i in cities:
        model.addConstr(
            gp.quicksum(x[i, j] for j in cities if j != i) == 1,
            name=f"out_{i}"
        )

    # Each city has exactly one incoming arc
    for j in cities:
        model.addConstr(
            gp.quicksum(x[i, j] for i in cities if i != j) == 1,
            name=f"in_{j}"
        )

    # MTZ subtour elimination constraints
    # If x[i,j] = 1 (and j != 0), then u[j] >= u[i] + 1
    for i in cities:
        for j in cities:
            if i != j and j != 0:
                model.addConstr(
                    u[j] >= u[i] + 1 - n * (1 - x[i, j]),
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