import gurobipy as gp
from gurobipy import GRB

def solve(params):
    distance_matrix = params["distance_matrix"]
    num_nodes = params["num_nodes"]
    num_pairs = params["num_pairs"]

    pickup_delivery_pairs = [[4, 5], [6, 1], [2, 3]]
    nodes = list(range(num_nodes))

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # x[i,j] = 1 if vehicle travels from i to j
    x = model.addVars(nodes, nodes, vtype=GRB.BINARY, name="x")

    # u[i] = position of node i in the tour (MTZ subtour elimination)
    u = model.addVars(nodes, vtype=GRB.CONTINUOUS, name="u")

    # Objective: minimize total travel cost
    model.setObjective(
        gp.quicksum(distance_matrix[i][j] * x[i, j] for i in nodes for j in nodes),
        GRB.MINIMIZE
    )

    # No self-loops
    for i in nodes:
        model.addConstr(x[i, i] == 0)

    # Each node is visited exactly once (one incoming arc)
    for j in nodes:
        model.addConstr(gp.quicksum(x[i, j] for i in nodes if i != j) == 1)

    # Each node is left exactly once (one outgoing arc)
    for i in nodes:
        model.addConstr(gp.quicksum(x[i, j] for j in nodes if j != i) == 1)

    # MTZ subtour elimination
    # u[0] = 0 (hub is start)
    model.addConstr(u[0] == 0)
    for i in nodes:
        if i != 0:
            model.addConstr(u[i] >= 1)
            model.addConstr(u[i] <= num_nodes - 1)

    for i in nodes:
        for j in nodes:
            if i != 0 and j != 0 and i != j:
                model.addConstr(u[i] - u[j] + (num_nodes - 1) * x[i, j] <= num_nodes - 2)

    # Pickup-delivery precedence constraints: pickup must come before delivery in the tour
    for pickup, delivery in pickup_delivery_pairs:
        model.addConstr(u[pickup] + 1 <= u[delivery])

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.TIME_LIMIT:
        return {"objective": None, "status": "time_limit"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}