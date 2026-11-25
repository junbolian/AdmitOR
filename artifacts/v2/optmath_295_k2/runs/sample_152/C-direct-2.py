import gurobipy as gp
from gurobipy import GRB

def solve(params):
    n = int(params["num_cities"])
    pos_lb = params["position_lower"]
    pos_ub = params["position_upper"]

    # Build cost matrix from params
    cost = {}
    for i in range(n):
        for j in range(n):
            if i != j:
                cost[i, j] = params[f"cost_{i}_{j}"]

    model = gp.Model("tsp")
    model.setParam("OutputFlag", 0)

    # x[i,j] = 1 if we travel from city i to city j
    x = model.addVars(
        [(i, j) for i in range(n) for j in range(n) if i != j],
        vtype=GRB.BINARY,
        name="x"
    )

    # u[i] = position of city i in the tour (MTZ formulation)
    u = model.addVars(n, lb=pos_lb, ub=pos_ub, vtype=GRB.CONTINUOUS, name="u")

    # Objective: minimize total travel cost
    model.setObjective(
        gp.quicksum(cost[i, j] * x[i, j] for i in range(n) for j in range(n) if i != j),
        GRB.MINIMIZE
    )

    # Each city is departed from exactly once
    for i in range(n):
        model.addConstr(
            gp.quicksum(x[i, j] for j in range(n) if j != i) == 1,
            name=f"depart_{i}"
        )

    # Each city is arrived at exactly once
    for j in range(n):
        model.addConstr(
            gp.quicksum(x[i, j] for i in range(n) if i != j) == 1,
            name=f"arrive_{j}"
        )

    # MTZ subtour elimination: u[i] - u[j] + n * x[i,j] <= n - 1
    # for all i != j, i != 0, j != 0
    for i in range(1, n):
        for j in range(1, n):
            if i != j:
                model.addConstr(
                    u[i] - u[j] + n * x[i, j] <= n - 1,
                    name=f"mtz_{i}_{j}"
                )

    # Fix position of depot
    model.addConstr(u[0] == 0, name="depot_pos")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.TIME_LIMIT:
        return {"objective": None, "status": "time_limit"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}