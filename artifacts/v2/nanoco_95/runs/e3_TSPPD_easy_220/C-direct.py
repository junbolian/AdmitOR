import gurobipy as gp
from gurobipy import GRB

def solve(params):
    coords = params["coords"]
    distance_matrix = params["distance_matrix"]

    num_nodes = len(coords)
    nodes = list(range(num_nodes))

    pickup_delivery_pairs = [[4, 3], [2, 6], [5, 1]]

    dist = {(i, j): distance_matrix[i][j] for i in nodes for j in nodes}

    model = gp.Model("library_pdp")
    model.setParam("OutputFlag", 0)

    # x[i,j] = 1 if van travels from i to j
    x = model.addVars(nodes, nodes, vtype=GRB.BINARY, name="x")

    # u[i] = position of node i in the tour (MTZ subtour elimination)
    u = model.addVars(nodes, vtype=GRB.CONTINUOUS, name="u")

    # Objective: minimize total distance
    model.setObjective(
        gp.quicksum(dist[i, j] * x[i, j] for i in nodes for j in nodes),
        GRB.MINIMIZE
    )

    # No self-loops
    for i in nodes:
        model.addConstr(x[i, i] == 0, name=f"no_self_{i}")

    # Each node is departed exactly once
    for i in nodes:
        model.addConstr(
            gp.quicksum(x[i, j] for j in nodes if j != i) == 1,
            name=f"depart_{i}"
        )

    # Each node is arrived at exactly once
    for j in nodes:
        model.addConstr(
            gp.quicksum(x[i, j] for i in nodes if i != j) == 1,
            name=f"arrive_{j}"
        )

    # MTZ subtour elimination
    # u[0] = 0, and for non-depot nodes u[i] in [1, num_nodes-1]
    model.addConstr(u[0] == 0, name="u_depot")
    for i in nodes:
        if i != 0:
            model.addConstr(u[i] >= 1, name=f"u_lb_{i}")
            model.addConstr(u[i] <= num_nodes - 1, name=f"u_ub_{i}")

    # MTZ linking constraints
    M = num_nodes
    for i in nodes:
        for j in nodes:
            if i != j and j != 0:
                model.addConstr(
                    u[i] - u[j] + M * x[i, j] <= M - 1,
                    name=f"mtz_{i}_{j}"
                )

    # Pickup before delivery precedence constraints
    for pickup, delivery in pickup_delivery_pairs:
        model.addConstr(
            u[pickup] + 1 <= u[delivery],
            name=f"precedence_{pickup}_{delivery}"
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