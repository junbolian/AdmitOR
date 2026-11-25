import gurobipy as gp
from gurobipy import GRB

def solve(params):
    distance_matrix = params["distance_matrix"]
    num_nodes = params["num_nodes"]

    nodes = list(range(num_nodes))

    model = gp.Model("tsp_waste")
    model.setParam("OutputFlag", 0)

    # Decision variables: x[i,j] = 1 if truck travels from i to j
    x = {}
    for i in nodes:
        for j in nodes:
            if i != j:
                x[i, j] = model.addVar(vtype=GRB.BINARY, name=f"x_{i}_{j}")

    # Subtour elimination variables (MTZ)
    u = {}
    for i in nodes:
        u[i] = model.addVar(lb=0, ub=num_nodes - 1, vtype=GRB.CONTINUOUS, name=f"u_{i}")

    model.update()

    # Objective: minimize total distance
    model.setObjective(
        gp.quicksum(distance_matrix[i][j] * x[i, j] for i in nodes for j in nodes if i != j),
        GRB.MINIMIZE
    )

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

    # MTZ subtour elimination constraints
    for i in nodes[1:]:
        for j in nodes[1:]:
            if i != j:
                model.addConstr(
                    u[i] - u[j] + (num_nodes - 1) * x[i, j] <= num_nodes - 2,
                    name=f"mtz_{i}_{j}"
                )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}