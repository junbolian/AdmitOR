import gurobipy as gp
from gurobipy import GRB

def solve(params):
    dispersion_scores = params["dispersion_scores"]
    facilities_to_select = params["facilities_to_select"]
    num_facilities = params["num_facilities"]

    nodes = list(range(num_facilities))
    # Ordered pairs (i,j) for i != j
    pairs = [(i, j) for i in nodes for j in nodes if i != j]

    # Map dispersion scores list to pairs
    score = {pairs[k]: dispersion_scores[k] for k in range(len(pairs))}

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Binary variable: whether facility i is selected
    x = model.addVars(nodes, vtype=GRB.BINARY, name="x")

    # Binary variable: whether ordered pair (i,j) is active
    z = model.addVars(pairs, vtype=GRB.BINARY, name="z")

    # Objective: maximize total dispersion score of active pairs
    model.setObjective(gp.quicksum(score[i, j] * z[i, j] for i, j in pairs), GRB.MAXIMIZE)

    # Exactly facilities_to_select facilities must be chosen
    model.addConstr(gp.quicksum(x[i] for i in nodes) == facilities_to_select, name="select_count")

    # Pair (i,j) is active only if both i and j are selected
    for i, j in pairs:
        model.addConstr(z[i, j] <= x[i], name=f"pair_i_{i}_{j}")
        model.addConstr(z[i, j] <= x[j], name=f"pair_j_{i}_{j}")
        model.addConstr(z[i, j] >= x[i] + x[j] - 1, name=f"pair_lb_{i}_{j}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}