import gurobipy as gp
from gurobipy import GRB

def solve(params):
    # Structural data: feasible order-station connections (certification compatibility)
    connections = [
        (0, 0), (0, 1), (0, 4),
        (1, 2),
        (2, 0), (2, 1), (2, 4),
        (3, 0), (3, 1), (3, 2),
        (4, 3),
    ]

    num_orders = 6
    num_stations = 5

    model = gp.Model("assignment")
    model.Params.OutputFlag = 0

    x = {}
    for (i, j) in connections:
        x[i, j] = model.addVar(vtype=GRB.BINARY, name=f"x_{i}_{j}")

    model.update()

    # Each order assigned to at most one station
    for i in range(num_orders):
        relevant = [x[i, j] for (o, j) in connections if o == i]
        if relevant:
            model.addConstr(gp.quicksum(relevant) <= 1, name=f"order_{i}")

    # Each station processes at most one order
    for j in range(num_stations):
        relevant = [x[i, j] for (i, k) in connections if k == j]
        if relevant:
            model.addConstr(gp.quicksum(relevant) <= 1, name=f"station_{j}")

    model.setObjective(gp.quicksum(x[i, j] for (i, j) in connections), GRB.MAXIMIZE)

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    else:
        return {"objective": None, "status": "failed"}