import gurobipy as gp
from gurobipy import GRB
import math

def solve(params):
    x_coords = params["x_coords"]
    y_coords = params["y_coords"]
    student_counts = params["student_counts"]
    num_schools = params["num_schools"]

    n = len(x_coords)
    villages = list(range(n))

    # Precompute Euclidean distances between all pairs of villages
    dist = {}
    for i in villages:
        for j in villages:
            dx = x_coords[i] - x_coords[j]
            dy = y_coords[i] - y_coords[j]
            dist[i, j] = math.sqrt(dx * dx + dy * dy)

    model = gp.Model("school_location")
    model.setParam("OutputFlag", 0)

    # y[j] = 1 if a school is built in village j
    y = model.addVars(villages, vtype=GRB.BINARY, name="y")

    # x_var[i, j] = 1 if village i is assigned to school in village j
    x_var = model.addVars(villages, villages, vtype=GRB.BINARY, name="x")

    # Objective: minimize total weighted walking distance
    model.setObjective(
        gp.quicksum(student_counts[i] * dist[i, j] * x_var[i, j]
                    for i in villages for j in villages),
        GRB.MINIMIZE
    )

    # Exactly num_schools schools are built
    model.addConstr(gp.quicksum(y[j] for j in villages) == num_schools, "num_schools")

    # Each village is assigned to exactly one school
    for i in villages:
        model.addConstr(gp.quicksum(x_var[i, j] for j in villages) == 1, f"assign_{i}")

    # Village i can only be assigned to village j if a school is built there
    for i in villages:
        for j in villages:
            model.addConstr(x_var[i, j] <= y[j], f"link_{i}_{j}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}