import gurobipy as gp
from gurobipy import GRB


def solve(params):
    dist = params["distance_matrix"]
    K = params["fleet_size"]
    n = 9  # nodes 0..8 (depot + 8 stops)
    stops = list(range(1, n))
    nn = len(stops)

    model = gp.Model("school_buses")
    model.Params.OutputFlag = 0

    # Arc usage variables (aggregate across identical buses)
    x = {}
    for i in range(n):
        for j in range(n):
            if i != j:
                x[i, j] = model.addVar(vtype=GRB.BINARY, name=f"x_{i}_{j}")

    # MTZ position variables for stops only
    u = {}
    for i in stops:
        u[i] = model.addVar(vtype=GRB.CONTINUOUS, lb=1, ub=nn, name=f"u_{i}")

    model.setObjective(
        gp.quicksum(dist[i][j] * x[i, j]
                   for i in range(n) for j in range(n) if i != j),
        GRB.MINIMIZE,
    )

    # Exactly K buses leave the depot
    model.addConstr(gp.quicksum(x[0, j] for j in range(1, n)) == K, name="depot_out")
    # Exactly K buses return to the depot
    model.addConstr(gp.quicksum(x[i, 0] for i in range(1, n)) == K, name="depot_in")

    # Each stop is entered exactly once
    for j in stops:
        model.addConstr(
            gp.quicksum(x[i, j] for i in range(n) if i != j) == 1,
            name=f"enter_{j}",
        )
    # Each stop is left exactly once
    for i in stops:
        model.addConstr(
            gp.quicksum(x[i, j] for j in range(n) if i != j) == 1,
            name=f"leave_{i}",
        )

    # MTZ subtour elimination (excludes depot, allows up to K depot-based tours)
    for i in stops:
        for j in stops:
            if i != j:
                model.addConstr(
                    u[i] - u[j] + nn * x[i, j] <= nn - 1,
                    name=f"mtz_{i}_{j}",
                )

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": "not_optimal"}