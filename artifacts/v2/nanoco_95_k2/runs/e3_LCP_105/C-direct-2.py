import gurobipy as gp
from gurobipy import GRB

def solve(params):
    num_slots = params["num_slots"]
    num_brands = params["num_brands"]
    adjacency_links = params["adjacency_links"]
    allowed_brands_per_slot = params["allowed_brands_per_slot"]

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # x[s, b] = 1 if slot s is assigned brand b
    x = {}
    for s in range(num_slots):
        allowed = allowed_brands_per_slot[s]
        for b in allowed:
            x[s, b] = model.addVar(vtype=GRB.BINARY, name=f"x_{s}_{b}")

    # z = max brand identifier used
    z = model.addVar(vtype=GRB.INTEGER, lb=0, ub=num_brands - 1, name="z")

    model.setObjective(z, GRB.MINIMIZE)

    # Each slot assigned exactly one brand from its allowed list
    for s in range(num_slots):
        allowed = allowed_brands_per_slot[s]
        model.addConstr(
            gp.quicksum(x[s, b] for b in allowed) == 1,
            name=f"assign_{s}"
        )

    # z >= b * x[s, b] for all s, b (z is at least the assigned brand id)
    for s in range(num_slots):
        allowed = allowed_brands_per_slot[s]
        for b in allowed:
            model.addConstr(z >= b * x[s, b], name=f"zbound_{s}_{b}")

    # Adjacency: adjacent slots cannot share the same brand
    for (s1, s2) in adjacency_links:
        shared = set(allowed_brands_per_slot[s1]) & set(allowed_brands_per_slot[s2])
        for b in shared:
            model.addConstr(
                x[s1, b] + x[s2, b] <= 1,
                name=f"adj_{s1}_{s2}_{b}"
            )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.TIME_LIMIT:
        return {"objective": None, "status": "time_limit"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}