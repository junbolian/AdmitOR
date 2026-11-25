import gurobipy as gp
from gurobipy import GRB
import numbers

def solve(params):
    preferences = params["preferences"]
    participant_capacity = params["participant_capacity"]
    car_capacity = params["car_capacity"]

    num_participants = len(preferences)
    num_cars = len(preferences[0]) if num_participants > 0 else 0

    def get_cap(cap, idx):
        if isinstance(cap, numbers.Number):
            return cap
        return cap[idx]

    model = gp.Model("car_assignment")
    model.Params.OutputFlag = 0

    x = {}
    for i in range(num_participants):
        for j in range(num_cars):
            if preferences[i][j] == 1:
                x[i, j] = model.addVar(vtype=GRB.BINARY, name=f"x_{i}_{j}")

    model.update()

    model.setObjective(gp.quicksum(x[i, j] for (i, j) in x), GRB.MAXIMIZE)

    for i in range(num_participants):
        vars_p = [x[i, j] for j in range(num_cars) if (i, j) in x]
        if vars_p:
            model.addConstr(gp.quicksum(vars_p) <= get_cap(participant_capacity, i))

    for j in range(num_cars):
        vars_c = [x[i, j] for i in range(num_participants) if (i, j) in x]
        if vars_c:
            model.addConstr(gp.quicksum(vars_c) <= get_cap(car_capacity, j))

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    else:
        return {"objective": None, "status": "infeasible" if model.status == GRB.INFEASIBLE else "failed"}