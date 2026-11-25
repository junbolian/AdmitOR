import gurobipy as gp
from gurobipy import GRB

def solve(params):
    weights = params["weights"]
    num_facilities = params["num_facilities"]

    n = 5
    nodes = range(n)
    pairs = [(i, j) for i in nodes for j in nodes if i != j]

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Binary variable: is node i selected?
    x = model.addVars(nodes, vtype=GRB.BINARY, name="x")

    # Binary variable: is pair (i,j) activated?
    z = model.addVars(pairs, vtype=GRB.BINARY, name="z")

    # Objective: maximize total weighted dispersion
    model.setObjective(
        gp.quicksum(weights[i][j] * z[i, j] for (i, j) in pairs),
        GRB.MAXIMIZE
    )

    # Exactly num_facilities selected
    model.addConstr(gp.quicksum(x[i] for i in nodes) == num_facilities, name="facility_count")

    # Pairwise activation constraints
    for (i, j) in pairs:
        # z[i,j] can be 1 only if both x[i] and x[j] are 1
        model.addConstr(z[i, j] <= x[i], name=f"act_i_{i}_{j}")
        model.addConstr(z[i, j] <= x[j], name=f"act_j_{i}_{j}")
        # If both are selected, z must be 1 (since we maximize, this is enforced by objective,
        # but adding it makes the formulation complete)
        model.addConstr(z[i, j] >= x[i] + x[j] - 1, name=f"act_lb_{i}_{j}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}