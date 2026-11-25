import gurobipy as gp
from gurobipy import GRB

def solve(params):
    weights = params["weights"]
    num_facilities = params["num_facilities"]

    # weights may be a dict with tuple keys, a nested list, or a dict of dicts
    # Normalize to a dict keyed by (i, j) tuples
    weight_dict = {}

    if isinstance(weights, dict):
        # Check if keys are tuples or integers
        sample_key = next(iter(weights))
        if isinstance(sample_key, tuple):
            # Already tuple-keyed dict
            weight_dict = {k: v for k, v in weights.items()}
        elif isinstance(sample_key, (int, str)):
            # Dict of dicts: weights[i][j] = value
            for i, row in weights.items():
                if isinstance(row, dict):
                    for j, val in row.items():
                        weight_dict[(i, j)] = val
                else:
                    # Row might be a list
                    for j, val in enumerate(row):
                        weight_dict[(i, j)] = val
    elif isinstance(weights, list):
        # Nested list: weights[i][j] = value
        for i, row in enumerate(weights):
            for j, val in enumerate(row):
                weight_dict[(i, j)] = val
    else:
        raise ValueError(f"Unsupported weights type: {type(weights)}")

    # Infer node set from weight_dict keys
    nodes = set()
    for (i, j) in weight_dict:
        nodes.add(i)
        nodes.add(j)
    nodes = sorted(nodes)
    pairs = list(weight_dict.keys())

    model = gp.Model("facility_dispersion")
    model.setParam("OutputFlag", 0)

    # Binary variables: x[i] = 1 if node i is selected
    x = model.addVars(nodes, vtype=GRB.BINARY, name="x")

    # Binary variables: y[i,j] = 1 if both i and j are selected
    y = model.addVars(pairs, vtype=GRB.BINARY, name="y")

    # Objective: maximize weighted dispersion
    model.setObjective(
        gp.quicksum(weight_dict[(i, j)] * y[i, j] for (i, j) in pairs),
        GRB.MAXIMIZE
    )

    # Exactly num_facilities selected
    model.addConstr(gp.quicksum(x[i] for i in nodes) == num_facilities, "facility_count")

    # Pairwise activation constraints
    for (i, j) in pairs:
        model.addConstr(y[i, j] <= x[i], f"pair_xi_{i}_{j}")
        model.addConstr(y[i, j] <= x[j], f"pair_xj_{i}_{j}")
        model.addConstr(y[i, j] >= x[i] + x[j] - 1, f"pair_lb_{i}_{j}")

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{status}"}