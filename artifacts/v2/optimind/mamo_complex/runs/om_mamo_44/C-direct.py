import gurobipy as gp
from gurobipy import GRB
from itertools import combinations

def solve(params):
    nodes = ['A', 'B', 'C', 'D', 'E']
    n = len(nodes)

    # Build cost dictionary from params
    cost = {}
    for i in nodes:
        for j in nodes:
            if i != j:
                cost[i, j] = params[f"cost_{i}{j}"]

    model = gp.Model("TSP")
    model.setParam("OutputFlag", 0)

    # Binary decision variables: x[i,j] = 1 if we travel from i to j
    x = model.addVars(
        [(i, j) for i in nodes for j in nodes if i != j],
        vtype=GRB.BINARY,
        name="x"
    )

    # Objective: minimize total travel cost
    model.setObjective(
        gp.quicksum(cost[i, j] * x[i, j] for i in nodes for j in nodes if i != j),
        GRB.MINIMIZE
    )

    # Each node must be left exactly once
    for i in nodes:
        model.addConstr(
            gp.quicksum(x[i, j] for j in nodes if j != i) == 1,
            name=f"leave_{i}"
        )

    # Each node must be entered exactly once
    for j in nodes:
        model.addConstr(
            gp.quicksum(x[i, j] for i in nodes if i != j) == 1,
            name=f"enter_{j}"
        )

    # Subtour elimination via MTZ formulation
    # u[i] = position of node i in the tour (for non-depot nodes)
    # We fix A as the depot reference
    depot = 'A'
    non_depot = [v for v in nodes if v != depot]

    u = model.addVars(non_depot, lb=1, ub=n - 1, vtype=GRB.CONTINUOUS, name="u")

    for i in non_depot:
        for j in non_depot:
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