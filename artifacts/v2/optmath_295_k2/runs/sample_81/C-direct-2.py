import gurobipy as gp
from gurobipy import GRB

def solve(params):
    crate_weight = params["crate_weight"]
    truck_capacity = params["truck_capacity"]

    n_crates = 10
    n_trucks = 10

    crates = range(n_crates)
    trucks = range(n_trucks)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # x[i, j] = 1 if crate i is assigned to truck j
    x = model.addVars(n_crates, n_trucks, vtype=GRB.BINARY, name="x")
    # y[j] = 1 if truck j is used
    y = model.addVars(n_trucks, vtype=GRB.BINARY, name="y")

    # Minimize number of trucks used
    model.setObjective(gp.quicksum(y[j] for j in trucks), GRB.MINIMIZE)

    # Each crate assigned to exactly one truck
    for i in crates:
        model.addConstr(gp.quicksum(x[i, j] for j in trucks) == 1, name=f"assign_{i}")

    # Capacity constraint per truck
    for j in trucks:
        model.addConstr(
            gp.quicksum(crate_weight * x[i, j] for i in crates) <= truck_capacity * y[j],
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