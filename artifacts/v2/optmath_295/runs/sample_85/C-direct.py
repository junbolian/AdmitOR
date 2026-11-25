import gurobipy as gp
from gurobipy import GRB

def solve(params):
    pref = {}
    pref[(0, 2)] = params["pref_0_2"]
    pref[(0, 5)] = params["pref_0_5"]
    pref[(1, 0)] = params["pref_1_0"]
    pref[(1, 1)] = params["pref_1_1"]
    pref[(1, 3)] = params["pref_1_3"]
    pref[(2, 0)] = params["pref_2_0"]
    pref[(2, 2)] = params["pref_2_2"]
    pref[(3, 1)] = params["pref_3_1"]
    pref[(3, 3)] = params["pref_3_3"]
    pref[(3, 4)] = params["pref_3_4"]
    pref[(5, 0)] = params["pref_5_0"]
    pref[(5, 3)] = params["pref_5_3"]

    participant_capacity = params["participant_capacity"]
    car_capacity = params["car_capacity"]
    num_participants = int(params["num_participants"])
    num_cars = int(params["num_cars"])
    coeff = params["assignment_coefficient"]

    valid_pairs = [(i, j) for (i, j), v in pref.items() if v > 0]

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    x = model.addVars(valid_pairs, vtype=GRB.BINARY, name="x")

    model.setObjective(
        gp.quicksum(coeff * x[i, j] for (i, j) in valid_pairs),
        GRB.MAXIMIZE
    )

    for pi in range(num_participants):
        pairs_i = [(i, j) for (i, j) in valid_pairs if i == pi]
        if pairs_i:
            model.addConstr(
                gp.quicksum(x[i, j] for (i, j) in pairs_i) <= participant_capacity,
                name=f"participant_{pi}"
            )

    for cj in range(num_cars):
        pairs_j = [(i, j) for (i, j) in valid_pairs if j == cj]
        if pairs_j:
            model.addConstr(
                gp.quicksum(x[i, j] for (i, j) in pairs_j) <= car_capacity,
                name=f"car_{cj}"
            )

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{status}"}