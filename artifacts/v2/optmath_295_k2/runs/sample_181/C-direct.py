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

    model = gp.Model("TSP")
    model.setParam("OutputFlag", 0)

    # Binary decision variables: x[i,j] = 1 if travel from city i to city j
    x = model.addVars(cities, cities, vtype=GRB.BINARY, name="x")

    # Auxiliary position variables for MTZ subtour elimination
    u = model.addVars(cities, vtype=GRB.CONTINUOUS, name="u")

    # Objective: minimize total cost
    model.setObjective(
        gp.quicksum(cost[i, j] * x[i, j] for i in cities for j in cities if i != j),
        GRB.MINIMIZE
    )

    # Each city is departed exactly once
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

    # No self-loops
    for i in cities:
        model.addConstr(x[i, i] == 0, name=f"no_self_{i}")

    # MTZ subtour elimination constraints for i=1..4, j=1..4
    for i in range(1, n):
        model.addConstr(u[i] >= u_lower, name=f"u_lb_{i}")
        model.addConstr(u[i] <= u_upper, name=f"u_ub_{i}")

    for i in range(1, n):
        for j in range(1, n):
            if i != j:
                model.addConstr(
                    u[i] - u[j] + n * x[i, j] <= n - 1,
                    name=f"mtz_{i}_{j}"
                )

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver_status_{status}"}