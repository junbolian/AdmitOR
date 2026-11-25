import gurobipy as gp
from gurobipy import GRB

def solve(params):
    supply_weights = params["supply_weights"]
    hospital_capacity = params["hospital_capacity"]

    n_supplies = len(supply_weights)
    n_hospitals = n_supplies  # worst case: one supply per hospital

    model = gp.Model("medical_supply_distribution")
    model.setParam("OutputFlag", 0)

    # x[i][j] = 1 if supply i is assigned to hospital j
    x = [[model.addVar(vtype=GRB.BINARY, name=f"x_{i}_{j}")
          for j in range(n_hospitals)]
         for i in range(n_supplies)]

    # y[j] = 1 if hospital j is used
    y = [model.addVar(vtype=GRB.BINARY, name=f"y_{j}")
         for j in range(n_hospitals)]

    # Objective: minimize number of hospitals used
    model.setObjective(gp.quicksum(y[j] for j in range(n_hospitals)), GRB.MINIMIZE)

    # Each supply assigned to exactly one hospital
    for i in range(n_supplies):
        model.addConstr(
            gp.quicksum(x[i][j] for j in range(n_hospitals)) == 1,
            name=f"assign_{i}"
        )

    # Capacity constraints
    for j in range(n_hospitals):
        model.addConstr(
            gp.quicksum(supply_weights[i] * x[i][j] for i in range(n_supplies)) <= hospital_capacity * y[j],
            name=f"capacity_{j}"
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