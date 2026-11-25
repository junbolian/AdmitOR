import gurobipy as gp
from gurobipy import GRB

def solve(params):
    supply_weights = params["supply_weights"]
    hospital_capacity = params["hospital_capacity"]

    n_supplies = len(supply_weights)  # 7
    n_hospitals = n_supplies          # upper bound: at most one supply per hospital

    supplies = range(n_supplies)
    hospitals = range(n_hospitals)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # x[i, j] = 1 if supply i is assigned to hospital j
    x = model.addVars(supplies, hospitals, vtype=GRB.BINARY, name="x")

    # y[j] = 1 if hospital j is used
    y = model.addVars(hospitals, vtype=GRB.BINARY, name="y")

    # Objective: minimize number of hospitals used
    model.setObjective(gp.quicksum(y[j] for j in hospitals), GRB.MINIMIZE)

    # Each supply assigned to exactly one hospital
    for i in supplies:
        model.addConstr(gp.quicksum(x[i, j] for j in hospitals) == 1, name=f"assign_{i}")

    # Capacity constraints
    for j in hospitals:
        model.addConstr(
            gp.quicksum(supply_weights[i] * x[i, j] for i in supplies) <= hospital_capacity * y[j],
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