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
                key = f"cost_{i}_{j}"
                cost[i, j] = params[key]

    model = gp.Model("TSP")
    model.setParam("OutputFlag", 0)

    # Binary decision variables x[i,j] = 1 if courier travels from i to j
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
    first = locations[0]
    model.addConstr(u[first] == 1, name="u_start")

    for i in locations:
        if i != first:
            model.addConstr(u[i] >= 2, name=f"u_lb_{i}")
            model.addConstr(u[i] <= n, name=f"u_ub_{i}")

    for i in locations:
        for j in locations:
            if i != j and i != first and j != first:
                model.addConstr(
                    u[i] - u[j] + n * x[i, j] <= n - 1,
                    name=f"mtz_{i}_{j}"
                )
            elif i != first and j == first:
                pass  # no constraint needed for arcs going back to start in MTZ
            elif i == first and j != first:
                pass

    # Standard MTZ for all non-depot pairs
    # Re-do properly: MTZ applies to all i != first
    # Clear previous MTZ constraints and redo
    # Actually the above loop already covers i != first and j != first
    # We also need constraints for arcs from first to others and others to first
    # Standard MTZ: for i != 0, j != 0, i != j: u[i] - u[j] + n*x[i,j] <= n-1
    # This is what we have. It's correct.

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}