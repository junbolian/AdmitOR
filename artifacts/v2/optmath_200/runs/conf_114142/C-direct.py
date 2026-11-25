import gurobipy as gp
from gurobipy import GRB

def solve(params):
    dispersion_weights = params["dispersion_weights"]
    total_facilities = params["total_facilities"]

    n = 5
    nodes = list(range(n))

    # Build ordered pairs (i,j) i!=j in the specified order
    pairs = [(i, j) for i in nodes for j in nodes if i != j]
    # pairs should be 20 entries matching the order given
    weight = {pairs[k]: dispersion_weights[k] for k in range(len(pairs))}

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Binary: select node i
    x = model.addVars(nodes, vtype=GRB.BINARY, name="x")

    # Binary: pairwise dispersion activated for (i,j)
    y = model.addVars(pairs, vtype=GRB.BINARY, name="y")

    # Objective: maximize total weighted dispersion
    model.setObjective(
        gp.quicksum(weight[i, j] * y[i, j] for (i, j) in pairs),
        GRB.MAXIMIZE
    )

    # Exactly total_facilities selected
    model.addConstr(gp.quicksum(x[i] for i in nodes) == total_facilities, name="total_facilities")

    # Pairwise logic constraints
    for (i, j) in pairs:
        # y[i,j] <= x[i]
        model.addConstr(y[i, j] <= x[i], name=f"y_xi_{i}_{j}")
        # y[i,j] <= x[j]
        model.addConstr(y[i, j] <= x[j], name=f"y_xj_{i}_{j}")
        # y[i,j] >= x[i] + x[j] - 1
        model.addConstr(y[i, j] >= x[i] + x[j] - 1, name=f"y_lb_{i}_{j}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}