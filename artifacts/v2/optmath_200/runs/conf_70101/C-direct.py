import gurobipy as gp
from gurobipy import GRB

def solve(params):
    n = 5
    nodes = list(range(n))
    pairs = [(i, j) for i in nodes for j in nodes if i != j]

    scores = {(i, j): params[f"pair_score_{i}_{j}"] for i, j in pairs}

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Binary variable: x[i] = 1 if site i is selected
    x = model.addVars(nodes, vtype=GRB.BINARY, name="x")

    # Binary variable: z[i,j] = 1 if both i and j are selected
    z = model.addVars(pairs, vtype=GRB.BINARY, name="z")

    # Exactly two sites selected
    model.addConstr(gp.quicksum(x[i] for i in nodes) == 2, name="select_two")

    # Linearization constraints: z[i,j] = x[i] * x[j]
    for i, j in pairs:
        model.addConstr(z[i, j] <= x[i], name=f"z_leq_xi_{i}_{j}")
        model.addConstr(z[i, j] <= x[j], name=f"z_leq_xj_{i}_{j}")
        model.addConstr(z[i, j] >= x[i] + x[j] - 1, name=f"z_geq_{i}_{j}")

    # Maximize total dispersion score
    model.setObjective(
        gp.quicksum(scores[i, j] * z[i, j] for i, j in pairs),
        GRB.MAXIMIZE
    )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}