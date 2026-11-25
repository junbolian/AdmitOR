import gurobipy as gp
from gurobipy import GRB
from itertools import combinations

def solve(params):
    num_trucks = params["num_trucks"]
    num_sites = params["num_sites"]
    travel_cost = params["travel_cost"]  # (num_sites+1) x (num_sites+1) matrix

    n = num_sites + 1  # total nodes including depot (node 0)
    depot = 0
    sites = list(range(1, n))
    nodes = list(range(n))
    trucks = list(range(num_trucks))

    # cost[i][j]
    c = {(i, j): travel_cost[i][j] for i in nodes for j in nodes if i != j}

    model = gp.Model("mobile_food_bank_vrp")
    model.setParam("OutputFlag", 0)

    # x[k,i,j] = 1 if truck k travels from i to j
    x = model.addVars(
        [(k, i, j) for k in trucks for i in nodes for j in nodes if i != j],
        vtype=GRB.BINARY,
        name="x"
    )

    # Objective: minimize total travel cost
    model.setObjective(
        gp.quicksum(c[i, j] * x[k, i, j] for k in trucks for i in nodes for j in nodes if i != j),
        GRB.MINIMIZE
    )

    # Each site visited exactly once across all trucks
    for j in sites:
        model.addConstr(
            gp.quicksum(x[k, i, j] for k in trucks for i in nodes if i != j) == 1,
            name=f"visit_{j}"
        )

    # Each truck departs depot at most once
    for k in trucks:
        model.addConstr(
            gp.quicksum(x[k, depot, j] for j in sites) <= 1,
            name=f"depart_{k}"
        )

    # Each truck returns to depot at most once
    for k in trucks:
        model.addConstr(
            gp.quicksum(x[k, i, depot] for i in sites) <= 1,
            name=f"return_{k}"
        )

    # Flow conservation at each site for each truck
    for k in trucks:
        for v in sites:
            model.addConstr(
                gp.quicksum(x[k, i, v] for i in nodes if i != v) ==
                gp.quicksum(x[k, v, j] for j in nodes if j != v),
                name=f"flow_{k}_{v}"
            )

    # All trucks must be used (each departs exactly once)
    for k in trucks:
        model.addConstr(
            gp.quicksum(x[k, depot, j] for j in sites) == 1,
            name=f"must_depart_{k}"
        )

    # MTZ subtour elimination
    # u[k,i] = position of node i in truck k's route
    u = model.addVars(
        [(k, i) for k in trucks for i in sites],
        lb=1.0, ub=float(num_sites),
        vtype=GRB.CONTINUOUS,
        name="u"
    )

    for k in trucks:
        for i in sites:
            for j in sites:
                if i != j:
                    model.addConstr(
                        u[k, i] - u[k, j] + num_sites * x[k, i, j] <= num_sites - 1,
                        name=f"mtz_{k}_{i}_{j}"
                    )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.TIME_LIMIT:
        return {"objective": None, "status": "time_limit"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}