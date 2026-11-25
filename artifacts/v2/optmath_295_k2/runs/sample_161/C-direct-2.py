import gurobipy as gp
from gurobipy import GRB

def solve(params):
    n = 7
    cities = list(range(n))

    # Build cost dict from params
    cost = {}
    for i in cities:
        for j in cities:
            if i != j:
                cost[i, j] = params[f"cost_{i}_{j}"]

    model = gp.Model("TSP")
    model.setParam("OutputFlag", 0)

    # Binary decision variables: x[i,j] = 1 if route i->j is taken
    x = model.addVars(
        [(i, j) for i in cities for j in cities if i != j],
        vtype=GRB.BINARY,
        name="x"
    )

    # MTZ position variables: u[i] for i in 1..n-1
    u = model.addVars(cities[1:], vtype=GRB.CONTINUOUS, lb=0, ub=n - 1, name="u")

    # Objective: minimize total travel cost
    model.setObjective(
        gp.quicksum(cost[i, j] * x[i, j] for i in cities for j in cities if i != j),
        GRB.MINIMIZE
    )

    # Each city is arrived at exactly once
    for j in cities:
        model.addConstr(
            gp.quicksum(x[i, j] for i in cities if i != j) == 1,
            name=f"arrive_{j}"
        )

    # Each city is departed from exactly once
    for i in cities:
        model.addConstr(
            gp.quicksum(x[i, j] for j in cities if i != j) == 1,
            name=f"depart_{i}"
        )

    # MTZ subtour elimination constraints (for i,j in 1..n-1, i != j)
    for i in cities[1:]:
        for j in cities[1:]:
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
    elif model.Status == GRB.TIME_LIMIT:
        return {"objective": None, "status": "time_limit"}
    else:
        return {"objective": None, "status": f"gurobi_status_{model.Status}"}