import gurobipy as gp
from gurobipy import GRB

def solve(params):
    n = 4
    cities = list(range(n))
    depot = 0
    non_depot = [1, 2, 3]

    cost = {}
    for i in cities:
        for j in cities:
            if i != j:
                cost[i, j] = params[f"travel_cost_{i}_{j}"]

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    x = model.addVars(cities, cities, vtype=GRB.BINARY,
                      name="x")
    for i in cities:
        model.addConstr(x[i, i] == 0)

    u = model.addVars(cities, vtype=GRB.CONTINUOUS, name="u")

    model.addConstr(u[depot] == params["u_depot_fixed"])
    lb = params["u_bound_lower"]
    ub = params["u_bound_upper"]
    for i in non_depot:
        u[i].lb = lb
        u[i].ub = ub

    # Each city visited exactly once (one incoming arc)
    for j in cities:
        model.addConstr(gp.quicksum(x[i, j] for i in cities if i != j) == 1)

    # Each city departed exactly once (one outgoing arc)
    for i in cities:
        model.addConstr(gp.quicksum(x[i, j] for j in cities if j != i) == 1)

    # MTZ subtour elimination for non-depot pairs
    M = ub - lb + 1
    for i in non_depot:
        for j in non_depot:
            if i != j:
                model.addConstr(u[i] - u[j] + M * x[i, j] <= M - 1)

    model.setObjective(
        gp.quicksum(cost[i, j] * x[i, j] for i in cities for j in cities if i != j),
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
        return {"objective": None, "status": f"solver_status_{model.Status}"}