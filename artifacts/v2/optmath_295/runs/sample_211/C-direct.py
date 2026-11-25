import gurobipy as gp
from gurobipy import GRB

def solve(params):
    n = 5
    cities = list(range(n))

    cost = {}
    for i in cities:
        for j in cities:
            if i != j:
                cost[i, j] = params[f"cost_{i}_{j}"]

    model = gp.Model("TSP")
    model.setParam("OutputFlag", 0)

    # Binary decision variables: x[i,j] = 1 if we travel from city i to city j
    x = model.addVars(cities, cities, vtype=GRB.BINARY, name="x")
    # Position variables for MTZ subtour elimination
    u = model.addVars(cities, vtype=GRB.CONTINUOUS, name="u", lb=0, ub=n - 1)

    # No self-loops
    for i in cities:
        model.addConstr(x[i, i] == 0, name=f"no_self_{i}")

    # Each city is departed exactly once
    for i in cities:
        model.addConstr(gp.quicksum(x[i, j] for j in cities if j != i) == 1, name=f"depart_{i}")

    # Each city is arrived at exactly once
    for j in cities:
        model.addConstr(gp.quicksum(x[i, j] for i in cities if i != j) == 1, name=f"arrive_{j}")

    # MTZ subtour elimination constraints (applied to non-depot cities)
    # Fix depot position to 0
    model.addConstr(u[0] == 0, name="depot_pos")

    for i in cities[1:]:
        model.addConstr(u[i] >= 1, name=f"u_lb_{i}")
        model.addConstr(u[i] <= n - 1, name=f"u_ub_{i}")

    for i in cities:
        for j in cities[1:]:
            if i != j:
                model.addConstr(
                    u[i] - u[j] + n * x[i, j] <= n - 1,
                    name=f"mtz_{i}_{j}"
                )

    # Objective: minimize total travel cost
    model.setObjective(
        gp.quicksum(cost[i, j] * x[i, j] for i in cities for j in cities if i != j),
        GRB.MINIMIZE
    )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.TIME_LIMIT:
        return {"objective": None, "status": "time_limit"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}