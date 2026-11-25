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
                key = f"travel_cost_{i}_{j}"
                cost[i, j] = params[key]

    u_lb = params["u_bound_lower"]
    u_ub = params["u_bound_upper"]
    u_depot = params["u_depot_fixed"]

    model = gp.Model("TSP")
    model.setParam("OutputFlag", 0)

    x = model.addVars(cities, cities, vtype=GRB.BINARY, name="x")
    for i in cities:
        model.addConstr(x[i, i] == 0, name=f"no_self_{i}")

    u = model.addVars(cities, vtype=GRB.CONTINUOUS, name="u")
    model.addConstr(u[depot] == u_depot, name="depot_pos")
    for i in non_depot:
        model.addConstr(u[i] >= u_lb, name=f"u_lb_{i}")
        model.addConstr(u[i] <= u_ub, name=f"u_ub_{i}")

    # Each city visited exactly once (one incoming arc)
    for j in cities:
        model.addConstr(gp.quicksum(x[i, j] for i in cities if i != j) == 1, name=f"in_{j}")

    # Each city departed exactly once (one outgoing arc)
    for i in cities:
        model.addConstr(gp.quicksum(x[i, j] for j in cities if j != i) == 1, name=f"out_{i}")

    # MTZ subtour elimination for non-depot cities
    big_m = n - 1
    for i in non_depot:
        for j in non_depot:
            if i != j:
                model.addConstr(
                    u[i] - u[j] + big_m * x[i, j] <= big_m - 1,
                    name=f"mtz_{i}_{j}"
                )

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
        return {"objective": None, "status": f"status_{model.Status}"}