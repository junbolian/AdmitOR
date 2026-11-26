import gurobipy as gp
from gurobipy import GRB

def solve(params):
    c12 = params["c12"]
    c13 = params["c13"]
    c14 = params["c14"]
    c21 = params["c21"]
    c23 = params["c23"]
    c24 = params["c24"]
    c31 = params["c31"]
    c32 = params["c32"]
    c34 = params["c34"]
    c41 = params["c41"]
    c42 = params["c42"]
    c43 = params["c43"]

    # Cities: 1, 2, 3, 4 (using 0-indexed internally: 0,1,2,3)
    n = 4
    cities = list(range(n))

    # Cost matrix (0-indexed): cost[i][j] = cost from city i+1 to city j+1
    cost = {
        (0, 1): c12, (0, 2): c13, (0, 3): c14,
        (1, 0): c21, (1, 2): c23, (1, 3): c24,
        (2, 0): c31, (2, 1): c32, (2, 3): c34,
        (3, 0): c41, (3, 1): c42, (3, 2): c43,
    }

    arcs = [(i, j) for i in cities for j in cities if i != j]

    model = gp.Model("TSP_4cities")
    model.setParam("OutputFlag", 0)

    # Binary decision variables: x[i,j] = 1 if arc (i->j) is used
    x = model.addVars(arcs, vtype=GRB.BINARY, name="x")

    # Subtour elimination auxiliary variables (MTZ formulation)
    # u[i] = position of city i in the tour (1-indexed, city 0 is fixed as start)
    u = model.addVars(cities, vtype=GRB.CONTINUOUS, name="u")

    # Objective: minimize total travel cost
    model.setObjective(
        gp.quicksum(cost[i, j] * x[i, j] for (i, j) in arcs),
        GRB.MINIMIZE
    )

    # Each city must be left exactly once
    for i in cities:
        model.addConstr(
            gp.quicksum(x[i, j] for j in cities if i != j) == 1,
            name=f"leave_{i}"
        )

    # Each city must be entered exactly once
    for j in cities:
        model.addConstr(
            gp.quicksum(x[i, j] for i in cities if i != j) == 1,
            name=f"enter_{j}"
        )

    # MTZ subtour elimination constraints
    # Fix position of city 0
    model.addConstr(u[0] == 0, name="u_start")
    for i in cities:
        model.addConstr(u[i] >= 0, name=f"u_lb_{i}")
        model.addConstr(u[i] <= n - 1, name=f"u_ub_{i}")

    # For non-depot cities i, j: u[i] - u[j] + n*x[i,j] <= n-1
    for i in cities:
        for j in cities:
            if i != j and j != 0:
                model.addConstr(
                    u[i] - u[j] + n * x[i, j] <= n - 1,
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
        return {"objective": None, "status": f"solver_status_{model.Status}"}