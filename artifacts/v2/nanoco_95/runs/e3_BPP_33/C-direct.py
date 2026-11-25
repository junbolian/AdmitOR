import gurobipy as gp
from gurobipy import GRB

def solve(params):
    item_sizes = params["item_sizes"]
    block_capacity = params["block_capacity"]

    n_items = len(item_sizes)
    # Upper bound on blocks needed: one per item
    n_blocks = n_items

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # x[i][j] = 1 if item i is assigned to block j
    x = [[model.addVar(vtype=GRB.BINARY, name=f"x_{i}_{j}")
          for j in range(n_blocks)]
         for i in range(n_items)]

    # y[j] = 1 if block j is used
    y = [model.addVar(vtype=GRB.BINARY, name=f"y_{j}")
         for j in range(n_blocks)]

    # Objective: minimize number of blocks used
    model.setObjective(gp.quicksum(y[j] for j in range(n_blocks)), GRB.MINIMIZE)

    # Each item must be assigned to exactly one block
    for i in range(n_items):
        model.addConstr(
            gp.quicksum(x[i][j] for j in range(n_blocks)) == 1,
            name=f"assign_{i}"
        )

    # Capacity constraint per block
    for j in range(n_blocks):
        model.addConstr(
            gp.quicksum(item_sizes[i] * x[i][j] for i in range(n_items)) <= block_capacity * y[j],
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