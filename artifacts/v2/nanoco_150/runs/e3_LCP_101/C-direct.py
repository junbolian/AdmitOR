import gurobipy as gp
from gurobipy import GRB

def solve(params):
    num_cells = params["num_cells"]
    num_links = params["num_links"]
    interference_links = params["interference_links"]
    frequency_pools = params["frequency_pools"]
    num_frequency_bands = params["num_frequency_bands"]

    bands = list(range(num_frequency_bands))

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # x[c, f] = 1 if cell c is assigned frequency band f
    x = {}
    for c in range(num_cells):
        for f in frequency_pools[c]:
            x[c, f] = model.addVar(vtype=GRB.BINARY, name=f"x_{c}_{f}")

    # z = maximum frequency band index used
    z = model.addVar(vtype=GRB.INTEGER, lb=0, ub=num_frequency_bands - 1, name="z")

    model.setObjective(z, GRB.MINIMIZE)

    # Each cell must be assigned exactly one frequency band from its pool
    for c in range(num_cells):
        model.addConstr(
            gp.quicksum(x[c, f] for f in frequency_pools[c]) == 1,
            name=f"assign_{c}"
        )

    # Adjacent cells must not share the same frequency band
    for idx, (c1, c2) in enumerate(interference_links):
        common_bands = set(frequency_pools[c1]) & set(frequency_pools[c2])
        for f in common_bands:
            model.addConstr(
                x[c1, f] + x[c2, f] <= 1,
                name=f"interference_{idx}_{f}"
            )

    # z >= f * x[c, f] for all c, f (z is the max band index used)
    for c in range(num_cells):
        for f in frequency_pools[c]:
            model.addConstr(
                z >= f * x[c, f],
                name=f"maxband_{c}_{f}"
            )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver_status_{model.Status}"}