import gurobipy as gp
from gurobipy import GRB


def solve(params):
    n = params["n_nodes"]
    cost = params["cost_matrix"]
    _coords = params["coords"]  # read per spec; cost matrix already encodes distances

    nodes = list(range(n))

    model = gp.Model("asymmetric_tsp")
    model.Params.OutputFlag = 0

    # x[i, j] = 1 if crew travels directly from site i to site j
    x = {}
    for i in nodes:
        for j in nodes:
            if i != j:
                x[i, j] = model.addVar(vtype=GRB.BINARY, name=f"x_{i}_{j}")

    # MTZ position variables for sites 1..n-1 (excludes base station 0)
    u = {}
    for i in nodes:
        if i != 0:
            u[i] = model.addVar(lb=1, ub=n - 1, vtype=GRB.CONTINUOUS, name=f"u_{i}")

    # Objective: minimize total travel cost
    model.setObjective(
        gp.quicksum(cost[i][j] * x[i, j] for i in nodes for j in nodes if i != j),
        GRB.MINIMIZE,
    )

    # Each site has exactly one outgoing edge
    for i in nodes:
        model.addConstr(
            gp.quicksum(x[i, j] for j in nodes if j != i) == 1,
            name=f"out_{i}",
        )

    # Each site has exactly one incoming edge
    for j in nodes:
        model.addConstr(
            gp.quicksum(x[i, j] for i in nodes if i != j) == 1,
            name=f"in_{j}",
        )

    # MTZ subtour elimination: forbids subtours that exclude the base station
    for i in nodes:
        if i == 0:
            continue
        for j in nodes:
            if j == 0 or j == i:
                continue
            model.addConstr(
                u[i] - u[j] + (n - 1) * x[i, j] <= n - 2,
                name=f"mtz_{i}_{j}",
            )

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}

    if model.status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}

    return {"objective": None, "status": f"status_{model.status}"}