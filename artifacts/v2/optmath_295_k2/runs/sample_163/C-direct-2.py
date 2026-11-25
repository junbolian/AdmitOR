import gurobipy as gp
from gurobipy import GRB

def solve(params):
    pairwise_benefits = params["pairwise_benefits"]
    num_selected = params["num_selected"]

    n = 5
    nodes = range(n)

    # Build ordered pairs list: (i, j) for i != j, row-major
    ordered_pairs = [(i, j) for i in nodes for j in nodes if i != j]

    # Map (i,j) -> benefit
    benefit = {}
    for idx, (i, j) in enumerate(ordered_pairs):
        benefit[(i, j)] = pairwise_benefits[idx]

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Binary variable: x[i] = 1 if node i is selected
    x = model.addVars(nodes, vtype=GRB.BINARY, name="x")

    # Binary variable: z[i][j] = 1 if both i and j are selected (i != j)
    z = model.addVars(ordered_pairs, vtype=GRB.BINARY, name="z")

    # Cardinality constraint
    model.addConstr(gp.quicksum(x[i] for i in nodes) == num_selected, name="cardinality")

    # Linearization constraints for z[i,j] = x[i] * x[j]
    for (i, j) in ordered_pairs:
        model.addConstr(z[i, j] <= x[i], name=f"z_xi_{i}_{j}")
        model.addConstr(z[i, j] <= x[j], name=f"z_xj_{i}_{j}")
        model.addConstr(z[i, j] >= x[i] + x[j] - 1, name=f"z_lb_{i}_{j}")

    # Objective: maximize total pairwise benefit
    model.setObjective(
        gp.quicksum(benefit[(i, j)] * z[i, j] for (i, j) in ordered_pairs),
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