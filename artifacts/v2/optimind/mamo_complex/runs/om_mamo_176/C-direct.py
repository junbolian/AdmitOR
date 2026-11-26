import gurobipy as gp
from gurobipy import GRB

def solve(params):
    cost_EF = params["cost_EF"]
    cost_EG = params["cost_EG"]
    cost_EH = params["cost_EH"]
    cost_FE = params["cost_FE"]
    cost_FG = params["cost_FG"]
    cost_FH = params["cost_FH"]
    cost_GE = params["cost_GE"]
    cost_GF = params["cost_GF"]
    cost_GH = params["cost_GH"]
    cost_HE = params["cost_HE"]
    cost_HF = params["cost_HF"]
    cost_HG = params["cost_HG"]
    num_locations = params["num_locations"]

    # Locations and cost matrix
    locations = ["E", "F", "G", "H"]
    n = num_locations  # should be 4

    cost = {
        ("E", "F"): cost_EF,
        ("E", "G"): cost_EG,
        ("E", "H"): cost_EH,
        ("F", "E"): cost_FE,
        ("F", "G"): cost_FG,
        ("F", "H"): cost_FH,
        ("G", "E"): cost_GE,
        ("G", "F"): cost_GF,
        ("G", "H"): cost_GH,
        ("H", "E"): cost_HE,
        ("H", "F"): cost_HF,
        ("H", "G"): cost_HG,
    }

    arcs = [(i, j) for i in locations for j in locations if i != j]

    model = gp.Model("TSP")
    model.setParam("OutputFlag", 0)

    # Binary decision variables: x[i,j] = 1 if courier travels from i to j
    x = model.addVars(arcs, vtype=GRB.BINARY, name="x")

    # Subtour elimination variables (MTZ formulation)
    # u[i] is the position of location i in the tour (continuous)
    u = model.addVars(locations, lb=0.0, ub=n - 1, vtype=GRB.CONTINUOUS, name="u")

    # Objective: minimize total cost
    model.setObjective(
        gp.quicksum(cost[i, j] * x[i, j] for (i, j) in arcs),
        GRB.MINIMIZE
    )

    # Each location must be left exactly once
    for i in locations:
        model.addConstr(
            gp.quicksum(x[i, j] for j in locations if j != i) == 1,
            name=f"leave_{i}"
        )

    # Each location must be entered exactly once
    for j in locations:
        model.addConstr(
            gp.quicksum(x[i, j] for i in locations if i != j) == 1,
            name=f"enter_{j}"
        )

    # MTZ subtour elimination constraints
    # Fix position of first location to break symmetry
    first = locations[0]  # "E"
    model.addConstr(u[first] == 0, name="u_start")

    for i in locations:
        for j in locations:
            if i != j and j != first:
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