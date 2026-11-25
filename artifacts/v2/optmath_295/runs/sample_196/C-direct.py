import gurobipy as gp
from gurobipy import GRB

def solve(params):
    truck_capacity = params["truck_capacity"]
    good_weights = params["good_weights"]

    n_goods = len(good_weights)
    n_trucks = n_goods  # upper bound: one good per truck

    goods = range(n_goods)
    trucks = range(n_trucks)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # x[i, j] = 1 if good i is assigned to truck j
    x = model.addVars(goods, trucks, vtype=GRB.BINARY, name="x")
    # y[j] = 1 if truck j is used
    y = model.addVars(trucks, vtype=GRB.BINARY, name="y")

    # Objective: minimize number of trucks used
    model.setObjective(gp.quicksum(y[j] for j in trucks), GRB.MINIMIZE)

    # Each good assigned to exactly one truck
    for i in goods:
        model.addConstr(gp.quicksum(x[i, j] for j in trucks) == 1, name=f"assign_{i}")

    # Capacity constraint per truck
    for j in trucks:
        model.addConstr(
            gp.quicksum(good_weights[i] * x[i, j] for i in goods) <= truck_capacity * y[j],
            name=f"capacity_{j}"
        )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}