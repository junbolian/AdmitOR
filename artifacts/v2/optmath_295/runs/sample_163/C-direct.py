import gurobipy as gp
from gurobipy import GRB

def solve(params):
    n_nodes = 5
    nodes = range(n_nodes)

    # Build coverage benefit matrix from params
    benefit = {}
    for i in nodes:
        for j in nodes:
            if i != j:
                key = f"coverage_benefit_{i}{j}"
                benefit[(i, j)] = params[key]

    num_centers = params["num_centers_to_select"]

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # x[i] = 1 if node i is selected
    x = model.addVars(nodes, vtype=GRB.BINARY, name="x")

    # z[i,j] = 1 if both node i and node j are selected
    z = model.addVars(
        [(i, j) for i in nodes for j in nodes if i != j],
        vtype=GRB.BINARY,
        name="z"
    )

    # Linearization constraints for z[i,j] = x[i] * x[j]
    for i in nodes:
        for j in nodes:
            if i != j:
                model.addConstr(z[i, j] <= x[i])
                model.addConstr(z[i, j] <= x[j])
                model.addConstr(z[i, j] >= x[i] + x[j] - 1)

    # Exactly num_centers nodes selected
    model.addConstr(gp.quicksum(x[i] for i in nodes) == num_centers)

    # Maximize total pairwise coverage benefit
    model.setObjective(
        gp.quicksum(benefit[(i, j)] * z[i, j] for i in nodes for j in nodes if i != j),
        GRB.MAXIMIZE
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