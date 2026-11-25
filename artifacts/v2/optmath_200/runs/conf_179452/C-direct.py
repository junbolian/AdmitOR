import gurobipy as gp
from gurobipy import GRB

def solve(params):
    dispersion_weights = params["dispersion_weights"]
    num_facilities_selected = params["num_facilities_selected"]

    n = 5
    nodes = range(n)

    # Normalize dispersion_weights to a dict keyed by (i,j)
    # Support: nested list (list of lists), flat list (row-major, i!=j pairs), or dict
    weights = {}
    if isinstance(dispersion_weights, dict):
        weights = dispersion_weights
    elif isinstance(dispersion_weights, list):
        if len(dispersion_weights) > 0 and isinstance(dispersion_weights[0], list):
            # Nested list: dispersion_weights[i][j]
            for i in nodes:
                for j in nodes:
                    if i != j:
                        weights[(i, j)] = dispersion_weights[i][j]
        else:
            # Flat list in row-major order over (i,j) pairs where i!=j
            # Order: (0,1),(0,2),(0,3),(0,4),(1,0),(1,2),...
            idx = 0
            for i in nodes:
                for j in nodes:
                    if i != j:
                        weights[(i, j)] = dispersion_weights[idx]
                        idx += 1
    else:
        # Try dict-like access
        weights = dispersion_weights

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Binary variable: whether facility i is selected
    x = model.addVars(nodes, vtype=GRB.BINARY, name="x")

    # Binary variable: whether both i and j are selected (pairwise)
    pairs = [(i, j) for i in nodes for j in nodes if i != j]
    y = model.addVars(pairs, vtype=GRB.BINARY, name="y")

    # Objective: maximize total weighted dispersion
    model.setObjective(
        gp.quicksum(
            weights[(i, j)] * y[i, j]
            for i in nodes for j in nodes if i != j
        ),
        GRB.MAXIMIZE
    )

    # Constraint: exactly num_facilities_selected facilities opened
    model.addConstr(
        gp.quicksum(x[i] for i in nodes) == num_facilities_selected,
        name="cardinality"
    )

    # Pairwise selection logic constraints
    for i in nodes:
        for j in nodes:
            if i == j:
                continue
            model.addConstr(y[i, j] <= x[i], name=f"pair_xi_{i}_{j}")
            model.addConstr(y[i, j] <= x[j], name=f"pair_xj_{i}_{j}")
            model.addConstr(y[i, j] >= x[i] + x[j] - 1, name=f"pair_lb_{i}_{j}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}