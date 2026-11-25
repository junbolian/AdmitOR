import gurobipy as gp
from gurobipy import GRB

def solve(params):
    memory_sizes = params["memory_sizes"]
    block_capacity = params["block_capacity"]

    n_objects = len(memory_sizes)
    # Upper bound on blocks needed: each object in its own block
    n_blocks = n_objects

    objects = range(n_objects)
    blocks = range(n_blocks)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # x[i,j] = 1 if object i is assigned to block j
    x = model.addVars(objects, blocks, vtype=GRB.BINARY, name="x")
    # y[j] = 1 if block j is used
    y = model.addVars(blocks, vtype=GRB.BINARY, name="y")

    # Minimize number of used blocks
    model.setObjective(gp.quicksum(y[j] for j in blocks), GRB.MINIMIZE)

    # Each object assigned to exactly one block
    for i in objects:
        model.addConstr(gp.quicksum(x[i, j] for j in blocks) == 1, name=f"assign_{i}")

    # Capacity constraint per block
    for j in blocks:
        model.addConstr(
            gp.quicksum(memory_sizes[i] * x[i, j] for i in objects) <= block_capacity * y[j],
            name=f"capacity_{j}"
        )

    # Symmetry breaking: block j can only be used if block j-1 is used
    for j in range(1, n_blocks):
        model.addConstr(y[j] <= y[j - 1], name=f"sym_{j}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.TIME_LIMIT:
        return {"objective": None, "status": "time_limit"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}