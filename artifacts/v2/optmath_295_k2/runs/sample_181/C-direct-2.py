import gurobipy as gp
from gurobipy import GRB

def solve(params):
    n = 5
    cities = list(range(n))

    cost = {}
    for i in cities:
        for j in cities:
            if i != j:
                key = f"cost_{i}_{j}"
                cost[i, j] = params[key]

    u_lower = params["u_lower"]
    u_upper = params["u_upper"]

    model = gp.Model()
    model.Params.OutputFlag = 0

    # Binary decision variables: x[i,j] = 1 if travel from city i to city j
    x = model.addVars(
        [(i, j) for i in cities for j in cities if i != j],
        vtype=GRB.BINARY,
        name="x"
    )

    # Auxiliary position variables for MTZ subtour elimination
    # u[0] is free; u[1..4] are bounded
    u = model.addVars(cities, vtype=GRB.CONTINUOUS, name="u")
    model.addConstr(u[0] >= 0)
    model.addConstr(u[0] <= n - 1)
    for i in range(1, n):
        model.addConstr(u[i] >= u_lower)
        model.addConstr(u[i] <= u_upper)

    # Objective: minimize total cost
    model.setObjective(
        gp.quicksum(cost[i, j] * x[i, j] for i in cities for j in cities if i != j),
        GRB.MINIMIZE
    )

    # Each city is departed from exactly once
    for i in cities:
        model.addConstr(
            gp.quicksum(x[i, j] for j in cities if j != i) == 1,
            name=f"depart_{i}"
        )

    # Each city is arrived at exactly once
    for j in cities:
        model.addConstr(
            gp.quicksum(x[i, j] for i in cities if i != j) == 1,
            name=f"arrive_{j}"
        )

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