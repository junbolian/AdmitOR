import gurobipy as gp
from gurobipy import GRB

def solve(params):
    locations = ['E', 'F', 'G', 'H', 'I']
    n = len(locations)
    idx = {loc: i for i, loc in enumerate(locations)}

    # Build cost matrix from params
    cost = {}
    for i in locations:
        for j in locations:
            if i != j:
                key = f"cost_{i}_to_{j}"
                cost[i, j] = params[key]

    model = gp.Model("TSP")
    model.setParam("OutputFlag", 0)

    # Binary decision variables: x[i,j] = 1 if courier goes from i to j
    x = model.addVars(locations, locations, vtype=GRB.BINARY, name="x")

    # Subtour elimination auxiliary variables (MTZ formulation)
    u = model.addVars(locations, vtype=GRB.CONTINUOUS, name="u")

    # Objective: minimize total cost
    model.setObjective(
        gp.quicksum(cost[i, j] * x[i, j] for i in locations for j in locations if i != j),
        GRB.MINIMIZE
    )

    # Each location is left exactly once
    for i in locations:
        model.addConstr(
            gp.quicksum(x[i, j] for j in locations if j != i) == 1,
            name=f"leave_{i}"
        )

    # Each location is entered exactly once
    for j in locations:
        model.addConstr(
            gp.quicksum(x[i, j] for i in locations if i != j) == 1,
            name=f"enter_{j}"
        )

    # MTZ subtour elimination constraints
    # Fix u for the first location to break symmetry
    start = locations[0]
    model.addConstr(u[start] == 1, name="u_start")
    for loc in locations[1:]:
        model.addConstr(u[loc] >= 2, name=f"u_lb_{loc}")
        model.addConstr(u[loc] <= n, name=f"u_ub_{loc}")

    for i in locations:
        for j in locations[1:]:  # j != start
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
    else:
        return {"objective": None, "status": f"status_{model.Status}"}