import gurobipy as gp
from gurobipy import GRB

def solve(params):
    n = int(params["num_cities"])
    cities = list(range(n))

    # Build distance matrix from params
    dist = {}
    for i in cities:
        for j in cities:
            if i != j:
                dist[i, j] = params[f"distance_{i}_{j}"]

    model = gp.Model("TSP")
    model.setParam("OutputFlag", 0)

    # Binary route selection variables
    x = {}
    for i in cities:
        for j in cities:
            if i != j:
                x[i, j] = model.addVar(vtype=GRB.BINARY, name=f"x_{i}_{j}")

    # Order variables for MTZ subtour elimination
    # u[0] is fixed, u[1..n-1] are bounded
    u = {}
    u[0] = model.addVar(lb=params["u0_fixed"], ub=params["u0_fixed"], vtype=GRB.CONTINUOUS, name="u_0")
    for i in range(1, n):
        u[i] = model.addVar(
            lb=params["u_lower_bound"],
            ub=params["u_upper_bound"],
            vtype=GRB.CONTINUOUS,
            name=f"u_{i}"
        )

    model.update()

    # Objective: minimize total distance
    model.setObjective(
        gp.quicksum(dist[i, j] * x[i, j] for i in cities for j in cities if i != j),
        GRB.MINIMIZE
    )

    # Each city has exactly one outgoing route
    for i in cities:
        model.addConstr(
            gp.quicksum(x[i, j] for j in cities if j != i) == 1,
            name=f"out_{i}"
        )

    # Each city has exactly one incoming route
    for j in cities:
        model.addConstr(
            gp.quicksum(x[i, j] for i in cities if i != j) == 1,
            name=f"in_{j}"
        )

    # MTZ subtour elimination constraints
    # For i != 0, j != 0, i != j: u[i] - u[j] + n * x[i,j] <= n - 1
    for i in range(1, n):
        for j in range(1, n):
            if i != j:
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
        return {"objective": None, "status": f"status_{model.Status}"}