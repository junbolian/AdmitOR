import gurobipy as gp
from gurobipy import GRB

def solve(params):
    coords = params["coords"]
    distance_matrix = params["distance_matrix"]

    n = len(coords)
    nodes = list(range(n))

    pickup_delivery_pairs = [[6, 3], [1, 5], [2, 4]]

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    x = model.addVars(nodes, nodes, vtype=GRB.BINARY, name="x")
    u = model.addVars(nodes, vtype=GRB.CONTINUOUS, name="u", lb=0, ub=n - 1)

    model.setObjective(
        gp.quicksum(distance_matrix[i][j] * x[i, j] for i in nodes for j in nodes),
        GRB.MINIMIZE
    )

    for i in nodes:
        model.addConstr(x[i, i] == 0)

    for i in nodes:
        model.addConstr(gp.quicksum(x[i, j] for j in nodes) == 1)

    for j in nodes:
        model.addConstr(gp.quicksum(x[i, j] for i in nodes) == 1)

    model.addConstr(u[0] == 0)
    for i in nodes[1:]:
        for j in nodes[1:]:
            if i != j:
                model.addConstr(u[i] - u[j] + (n - 1) * x[i, j] <= n - 2)

    # Precedence: u[pu] + 1 <= u[dv], i.e. pickup visited strictly before delivery
    for (pu, dv) in pickup_delivery_pairs:
        model.addConstr(u[pu] + 1 <= u[dv])

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}