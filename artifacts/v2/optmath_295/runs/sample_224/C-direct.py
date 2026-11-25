import gurobipy as gp
from gurobipy import GRB

def solve(params):
    n = 6
    cities = list(range(n))

    # Build cost matrix from params
    cost = {}
    for i in cities:
        for j in cities:
            if i != j:
                cost[i, j] = params[f"cost_{i}_{j}"]

    pos_lb = params["position_bound_lower"]
    pos_ub = params["position_bound_upper"]
    city0_pos = params["city0_position"]

    model = gp.Model("TSP")
    model.setParam("OutputFlag", 0)

    # Binary route variables
    x = {}
    for i in cities:
        for j in cities:
            if i != j:
                x[i, j] = model.addVar(vtype=GRB.BINARY, name=f"x_{i}_{j}")

    # Position variables for MTZ subtour elimination
    u = {}
    for i in cities:
        u[i] = model.addVar(lb=pos_lb, ub=pos_ub, vtype=GRB.CONTINUOUS, name=f"u_{i}")

    model.update()

    # Objective
    model.setObjective(
        gp.quicksum(cost[i, j] * x[i, j] for i in cities for j in cities if i != j),
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

    # Fix City 0 position
    model.addConstr(u[0] == city0_pos, name="fix_u0")

    # MTZ subtour elimination constraints for non-depot cities
    big_m = pos_ub - pos_lb
    for i in cities:
        for j in cities:
            if i != j and j != 0:
                model.addConstr(
                    u[i] - u[j] + big_m * x[i, j] <= big_m - 1,
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
        return {"objective": None, "status": f"status_{status}"}