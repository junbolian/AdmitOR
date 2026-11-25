import gurobipy as gp
from gurobipy import GRB

def solve(params):
    weights = params["weights"]
    num_facilities = params["num_facilities"]

    # Normalize weights keys: may be tuples (i,j) or nested dict or string keys
    # Build a clean dict: {(i,j): weight}
    clean_weights = {}
    for key, val in weights.items():
        if isinstance(key, tuple):
            clean_weights[key] = val
        elif isinstance(key, str):
            # Try parsing "i,j" or "(i,j)"
            key_stripped = key.strip().strip("()")
            parts = key_stripped.split(",")
            i, j = int(parts[0].strip()), int(parts[1].strip())
            clean_weights[(i, j)] = val
        elif isinstance(key, int):
            # weights is a flat dict indexed by integer, with val being another dict
            # i.e., weights[i][j] = w
            if isinstance(val, dict):
                for j, w in val.items():
                    clean_weights[(key, j)] = w
            else:
                raise ValueError(f"Unexpected weights format: key={key}, val={val}")
        else:
            raise ValueError(f"Unexpected key type: {type(key)}")

    pairs = list(clean_weights.keys())

    # Infer node set from pair keys
    nodes = set()
    for (i, j) in pairs:
        nodes.add(i)
        nodes.add(j)
    nodes = sorted(nodes)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Binary variable: whether node i is selected
    x = model.addVars(nodes, vtype=GRB.BINARY, name="x")

    # Binary variable: whether pair (i,j) is activated
    z = model.addVars(pairs, vtype=GRB.BINARY, name="z")

    # Objective: maximize total weighted dispersion
    model.setObjective(
        gp.quicksum(clean_weights[(i, j)] * z[(i, j)] for (i, j) in pairs),
        GRB.MAXIMIZE
    )

    # Exactly num_facilities selected
    model.addConstr(gp.quicksum(x[i] for i in nodes) == num_facilities, name="facility_count")

    # Pairwise activation constraints
    for (i, j) in pairs:
        model.addConstr(z[(i, j)] <= x[i], name=f"act_i_{i}_{j}")
        model.addConstr(z[(i, j)] <= x[j], name=f"act_j_{i}_{j}")
        model.addConstr(z[(i, j)] >= x[i] + x[j] - 1, name=f"act_lb_{i}_{j}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}