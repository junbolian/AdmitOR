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

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # x[i,j] = 1 if we travel from city i to city j
    x = model.addVars(
        [(i, j) for i in range(n) for j in range(n) if i != j],
        vtype=GRB.BINARY,
        name="x"
    )

    # u[i] = position of city i in the tour (MTZ variables)
    u = model.addVars(n, lb=pos_lb, ub=pos_ub, vtype=GRB.CONTINUOUS, name="u")

    # Objective: minimize total travel cost
    model.setObjective(
        gp.quicksum(cost[i, j] * x[i, j] for i in range(n) for j in range(n) if i != j),
        GRB.MINIMIZE
    )

    # Each city is entered exactly once
    for j in range(n):
        model.addConstr(
            gp.quicksum(x[i, j] for i in range(n) if i != j) == 1,
            name=f"enter_{j}"
        )

    # Each city is departed exactly once
    for i in range(n):
        model.addConstr(
            gp.quicksum(x[i, j] for j in range(n) if i != j) == 1,
            name=f"depart_{i}"
        )

    # MTZ subtour elimination
    # City 0 is the depot; fix its position to lower bound
    model.addConstr(u[0] == pos_lb, name="u0_fix")

    for i in range(1, n):
        for j in range(1, n):
            if i != j:
                model.addConstr(
                    u[i] - u[j] + (n - 1) * x[i, j] <= n - 2,
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
        return {"objective": None, "status": f"gurobi_status_{status}"}