import gurobipy as gp
from gurobipy import GRB

def solve(params):
    feasible = [
        (0, 0), (0, 2), (0, 3),
        (1, 4),
        (2, 0), (2, 1), (2, 2),
        (3, 0), (3, 2), (3, 4),
        (4, 0), (4, 2), (4, 3), (4, 4),
        (5, 0),
    ]

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    x = model.addVars(feasible, vtype=GRB.BINARY, name="x")

    model.setObjective(gp.quicksum(x[i, j] for (i, j) in feasible), GRB.MAXIMIZE)

    users = range(7)
    freqs = range(5)

    for i in users:
        pairs = [(i, j) for (i, j) in feasible if i == i and (i, j) in x]
        user_pairs = [(u, f) for (u, f) in feasible if u == i]
        if user_pairs:
            model.addConstr(gp.quicksum(x[u, f] for (u, f) in user_pairs) <= 1, name=f"user_{i}")

    for j in freqs:
        freq_pairs = [(u, f) for (u, f) in feasible if f == j]
        if freq_pairs:
            model.addConstr(gp.quicksum(x[u, f] for (u, f) in freq_pairs) <= 1, name=f"freq_{j}")

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver_status_{status}"}