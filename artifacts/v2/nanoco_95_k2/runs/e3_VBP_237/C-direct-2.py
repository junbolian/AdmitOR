import gurobipy as gp
from gurobipy import GRB


def solve(params):
    capacities = params["capacities"]
    weights = params["weights"]

    num_items = len(weights)
    num_dims = len(capacities)
    num_slots = num_items  # upper bound: one slot per item

    model = gp.Model("surgical_scheduling")
    model.setParam("OutputFlag", 0)

    # x[i, j] = 1 if procedure i is assigned to slot j
    x = {}
    for i in range(num_items):
        for j in range(num_slots):
            x[i, j] = model.addVar(vtype=GRB.BINARY, name=f"x_{i}_{j}")

    # y[j] = 1 if slot j is utilized
    y = {}
    for j in range(num_slots):
        y[j] = model.addVar(vtype=GRB.BINARY, name=f"y_{j}")

    model.update()

    # Each procedure must be assigned to exactly one slot
    for i in range(num_items):
        model.addConstr(
            gp.quicksum(x[i, j] for j in range(num_slots)) == 1,
            name=f"assign_{i}",
        )

    # Capacity constraints per slot and resource dimension
    for j in range(num_slots):
        for d in range(num_dims):
            model.addConstr(
                gp.quicksum(weights[i][d] * x[i, j] for i in range(num_items))
                <= capacities[d] * y[j],
                name=f"cap_{j}_{d}",
            )

    # Objective: minimize the number of utilized slots
    model.setObjective(
        gp.quicksum(y[j] for j in range(num_slots)), GRB.MINIMIZE
    )

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.objVal), "status": "optimal"}

    return {"objective": None, "status": f"gurobi_status_{model.status}"}