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

    model = gp.Model("tsp")
    model.setParam("OutputFlag", 0)

    # Binary decision variables: x[i,j] = 1 if travel from city i to city j
    x = model.addVars(cities, cities, vtype=GRB.BINARY, name="x")
    for i in cities:
        model.addConstr(x[i, i] == 0, name=f"no_self_{i}")

    # Position variables for MTZ subtour elimination (cities 1..4)
    u = model.addVars(cities, lb=1.0, ub=float(n - 1), vtype=GRB.CONTINUOUS, name="u")

    # Objective: minimize total cost
    model.setObjective(
        gp.quicksum(cost[i, j] * x[i, j] for i in cities for j in cities if i != j),
        GRB.MINIMIZE
    )

    # Each city is departed exactly once
    for i in cities:
        model.addConstr(gp.quicksum(x[i, j] for j in cities if j != i) == 1, name=f"depart_{i}")

    # Each city is arrived at exactly once
    for j in cities:
        model.addConstr(gp.quicksum(x[i, j] for i in cities if i != j) == 1, name=f"arrive_{j}")

    # MTZ subtour elimination: for i != 0, j != 0, i != j
    # u[j] >= u[i] + 1 - (n-1)*(1 - x[i,j])
    big_m = float(n - 1)
    for i in cities:
        for j in cities:
            if i != j and i != 0 and j != 0:
                model.addConstr(
                    u[j] >= u[i] + 1 - big_m * (1 - x[i, j]),
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