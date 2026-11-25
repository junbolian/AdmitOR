import gurobipy as gp
from gurobipy import GRB

def solve(params):
    D = params["distance_matrix"]
    n = 7
    required_edges = [(0, 1), (0, 5), (1, 5), (1, 6), (2, 3), (4, 6)]

    model = gp.Model("rpp")
    model.Params.OutputFlag = 0

    # x[i,j]: number of directed traversals from i to j
    x = {}
    for i in range(n):
        for j in range(n):
            if i != j:
                x[i, j] = model.addVar(vtype=GRB.INTEGER, lb=0, name=f"x_{i}_{j}")

    # f[i,j]: connectivity flow from depot to all nodes
    f = {}
    for i in range(n):
        for j in range(n):
            if i != j:
                f[i, j] = model.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"f_{i}_{j}")

    model.update()

    # Objective: minimize total travel distance
    model.setObjective(
        gp.quicksum(D[i][j] * x[i, j] for i in range(n) for j in range(n) if i != j),
        GRB.MINIMIZE,
    )

    # Required edges: service at least once in either direction
    for (a, b) in required_edges:
        model.addConstr(x[a, b] + x[b, a] >= 1, name=f"req_{a}_{b}")

    # Flow balance: arrivals = departures at every node (Eulerian condition)
    for i in range(n):
        model.addConstr(
            gp.quicksum(x[j, i] for j in range(n) if j != i)
            == gp.quicksum(x[i, j] for j in range(n) if j != i),
            name=f"balance_{i}",
        )

    # Connectivity: single-commodity flow from depot to all other nodes
    M = n - 1
    for i in range(n):
        for j in range(n):
            if i != j:
                model.addConstr(f[i, j] <= M * x[i, j], name=f"link_{i}_{j}")

    # Depot (node 0) sends n-1 units
    model.addConstr(
        gp.quicksum(f[0, j] for j in range(n) if j != 0)
        - gp.quicksum(f[j, 0] for j in range(n) if j != 0)
        == n - 1,
        name="flow_source",
    )

    # Each non-depot node receives 1 unit
    for i in range(1, n):
        model.addConstr(
            gp.quicksum(f[j, i] for j in range(n) if j != i)
            - gp.quicksum(f[i, j] for j in range(n) if j != i)
            == 1,
            name=f"flow_sink_{i}",
        )

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"failed_status_{model.status}"}