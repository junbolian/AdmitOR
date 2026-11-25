import gurobipy as gp
from gurobipy import GRB

def solve(params):
    n = int(params["n_cities"])
    pos_ub = int(params["position_upper_bound"])

    # Build cost dict from params
    cost = {}
    for i in range(n):
        for j in range(n):
            if i != j:
                key = f"cost_{i}_{j}"
                cost[(i, j)] = params[key]

    model = gp.Model("tsp")
    model.setParam("OutputFlag", 0)

    # x[i,j] = 1 if travel from city i to city j
    x = model.addVars(n, n, vtype=GRB.BINARY, name="x")
    # u[i] = position of city i in tour (MTZ formulation)
    u = model.addVars(n, lb=0, ub=pos_ub, vtype=GRB.CONTINUOUS, name="u")

    # No self-loops
    for i in range(n):
        model.addConstr(x[i, i] == 0, name=f"no_self_{i}")

    # Each city entered exactly once
    for j in range(n):
        model.addConstr(gp.quicksum(x[i, j] for i in range(n) if i != j) == 1, name=f"enter_{j}")

    # Each city departed exactly once
    for i in range(n):
        model.addConstr(gp.quicksum(x[i, j] for j in range(n) if j != i) == 1, name=f"depart_{i}")

    # MTZ subtour elimination: for i,j in {1..n-1}, i != j
    # u[i] - u[j] + n * x[i,j] <= n - 1
    for i in range(1, n):
        for j in range(1, n):
            if i != j:
                model.addConstr(
                    u[i] - u[j] + n * x[i, j] <= n - 1,
                    name=f"mtz_{i}_{j}"
                )

    # Fix depot position
    model.addConstr(u[0] == 0, name="depot_pos")

    # Objective: minimize total travel cost
    model.setObjective(
        gp.quicksum(cost[(i, j)] * x[i, j] for i in range(n) for j in range(n) if i != j),
        GRB.MINIMIZE
    )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"gurobi_status_{model.Status}"}