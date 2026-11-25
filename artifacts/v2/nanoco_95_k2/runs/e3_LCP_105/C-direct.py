import gurobipy as gp
from gurobipy import GRB


def solve(params):
    num_slots = params["num_slots"]
    num_brands = params["num_brands"]
    adjacency_links = params["adjacency_links"]
    allowed_brands_per_slot = params["allowed_brands_per_slot"]

    model = gp.Model("shelf_planning")
    model.setParam("OutputFlag", 0)

    # x[s, b] = 1 if slot s is assigned brand b (only created for allowed (s,b) pairs)
    x = {}
    for s in range(num_slots):
        for b in allowed_brands_per_slot[s]:
            x[s, b] = model.addVar(vtype=GRB.BINARY, name=f"x_{s}_{b}")

    # z = maximum brand identifier used across the shelf
    z = model.addVar(vtype=GRB.INTEGER, lb=0, ub=num_brands - 1, name="z")

    model.update()

    # Rule 1: each slot must be assigned exactly one brand from its permitted list
    for s in range(num_slots):
        model.addConstr(
            gp.quicksum(x[s, b] for b in allowed_brands_per_slot[s]) == 1,
            name=f"assign_{s}",
        )

    # Rule 2: adjacent slots must not share the same brand
    for link in adjacency_links:
        i, j = link[0], link[1]
        common_brands = set(allowed_brands_per_slot[i]) & set(allowed_brands_per_slot[j])
        for b in common_brands:
            model.addConstr(x[i, b] + x[j, b] <= 1, name=f"adj_{i}_{j}_{b}")

    # Objective link: z must be at least as large as any assigned brand identifier
    for s in range(num_slots):
        for b in allowed_brands_per_slot[s]:
            model.addConstr(z >= b * x[s, b], name=f"link_z_{s}_{b}")

    model.setObjective(z, GRB.MINIMIZE)
    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.objVal), "status": "optimal"}

    if model.status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}

    return {"objective": None, "status": "no_optimal"}