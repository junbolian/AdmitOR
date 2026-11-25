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
    x = {}
    for i in nodes:
        for j in nodes:
            if i != j:
                x[i, j] = model.addVar(vtype=GRB.BINARY, name=f"x_{i}_{j}")

    # u[i] = position of node i in the tour (MTZ formulation), u[0] = 0
    u = {}
    for i in nodes:
        u[i] = model.addVar(lb=0, ub=num_nodes - 1, vtype=GRB.CONTINUOUS, name=f"u_{i}")

    # Objective: minimize total travel cost
    model.setObjective(
        gp.quicksum(distance_matrix[i][j] * x[i, j] for i in nodes for j in nodes if i != j),
        GRB.MINIMIZE
    )

    # Each node is left exactly once
    for i in nodes:
        model.addConstr(gp.quicksum(x[i, j] for j in nodes if j != i) == 1, name=f"leave_{i}")

    # Each node is entered exactly once
    for j in nodes:
        model.addConstr(gp.quicksum(x[i, j] for i in nodes if i != j) == 1, name=f"enter_{j}")

    # MTZ subtour elimination
    for i in nodes:
        for j in nodes:
            if i != j and not (i == 0 or j == 0):
                model.addConstr(
                    u[i] - u[j] + (num_nodes - 1) * x[i, j] <= num_nodes - 2,
                    name=f"mtz_{i}_{j}"
                )

    # Hub is first in ordering
    model.addConstr(u[0] == 0, name="hub_start")

    # Precedence constraints: pickup must be visited before delivery
    for pickup, delivery in pickup_delivery_pairs:
        model.addConstr(u[pickup] + 1 <= u[delivery], name=f"prec_{pickup}_{delivery}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.TIME_LIMIT:
        return {"objective": None, "status": "time_limit"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}