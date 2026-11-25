import gurobipy as gp
from gurobipy import GRB


def solve(params):
    cost_matrix = params["cost_matrix"]
    num_doctors = params["num_doctors"]
    num_patients = params["num_patients"]

    model = gp.Model("doctor_patient_matching")
    model.Params.OutputFlag = 0

    x = {}
    for i in range(num_doctors):
        for j in range(num_patients):
            x[i, j] = model.addVar(vtype=GRB.BINARY, name=f"x_{i}_{j}")

    model.update()

    model.setObjective(
        gp.quicksum(cost_matrix[i][j] * x[i, j]
                    for i in range(num_doctors)
                    for j in range(num_patients)),
        GRB.MINIMIZE,
    )

    for i in range(num_doctors):
        model.addConstr(
            gp.quicksum(x[i, j] for j in range(num_patients)) == 1,
            name=f"doctor_assigned_{i}",
        )

    for j in range(num_patients):
        model.addConstr(
            gp.quicksum(x[i, j] for i in range(num_doctors)) <= 1,
            name=f"patient_at_most_one_{j}",
        )

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": "failed"}