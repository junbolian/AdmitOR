import gurobipy as gp
from gurobipy import GRB

def solve(params):
    pairwise_benefits = params["pairwise_benefits"]
    num_selected = params["num_selected"]

    n = 5
    # Build ordered pairs list: (i, j) for i != j, row-major
    ordered_pairs = [(i, j) for i in range(n) for j in range(n) if i != j]

    # Map (i,j) -> benefit
    w = {}
    for idx, (i, j) in enumerate(ordered_pairs):
        w[(i, j)] = pairwise_benefits[idx]

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # x[i] = 1 if node i is selected
    x = model.addVars(n, vtype=GRB.BINARY, name="x")

    # z[i,j] = 1 if both i and j are selected (linearization of x[i]*x[j])
    z = model.addVars(ordered_pairs, vtype=GRB.BINARY, name="z")

    # Cardinality constraint
    model.addConstr(gp.quicksum(x[i] for i in range(n)) == num_selected, name="cardinality")

    # Linearization constraints for z[i,j] = x[i] * x[j]
    for (i, j) in ordered_pairs:
        model.addConstr(z[i, j] <= x[i], name=f"z_xi_{i}_{j}")
        model.addConstr(z[i, j] <= x[j], name=f"z_xj_{i}_{j}")
        model.addConstr(z[i, j] >= x[i] + x[j] - 1, name=f"z_lb_{i}_{j}")

    # Objective: maximize total pairwise benefit
    model.setObjective(
        gp.quicksum(w[(i, j)] * z[i, j] for (i, j) in ordered_pairs),
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