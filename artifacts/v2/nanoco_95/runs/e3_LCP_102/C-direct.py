import gurobipy as gp
from gurobipy import GRB

def solve(params):
    incompatibility_pairs = params["incompatibility_pairs"]
    num_warehouse_zones = params["num_warehouse_zones"]

    allowed_types = {}
    for z in range(num_warehouse_zones):
        allowed_types[z] = params[f"zone_{z}_allowed_types"]

    # Collect all type indices that appear in any allowed list
    all_types = sorted(set(t for types in allowed_types.values() for t in types))

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # x[z, t] = 1 if zone z is assigned type t
    x = {}
    for z in range(num_warehouse_zones):
        for t in allowed_types[z]:
            x[z, t] = model.addVar(vtype=GRB.BINARY, name=f"x_{z}_{t}")

    # max_type: the maximum type index used
    max_type = model.addVar(lb=0, ub=max(all_types), name="max_type")

    model.setObjective(max_type, GRB.MINIMIZE)

    # Each zone assigned exactly one type from its allowed list
    for z in range(num_warehouse_zones):
        model.addConstr(
            gp.quicksum(x[z, t] for t in allowed_types[z]) == 1,
            name=f"assign_{z}"
        )

    # Incompatibility: pairs cannot share the same type
    for z1, z2 in incompatibility_pairs:
        shared_types = set(allowed_types[z1]) & set(allowed_types[z2])
        for t in shared_types:
            model.addConstr(
                x[z1, t] + x[z2, t] <= 1,
                name=f"incompat_{z1}_{z2}_{t}"
            )

    # max_type >= t * x[z, t] for all z, t
    for z in range(num_warehouse_zones):
        for t in allowed_types[z]:
            model.addConstr(
                max_type >= t * x[z, t],
                name=f"maxtype_{z}_{t}"
            )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.TIME_LIMIT:
        return {"objective": None, "status": "time_limit"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}