import gurobipy as gp
from gurobipy import GRB


def solve(params):
    num_participants = params["num_participants"]
    num_cars = params["num_cars"]
    preferences = [params["preference_{0}".format(i)] for i in range(num_participants)]

    model = gp.Model("car_assignment")
    model.ModelSense = GRB.MAXIMIZE

    x = {}
    for i in range(num_participants):
        for j in range(num_cars):
            if preferences[i][j] == 1:
                x[i, j] = model.addVar(vtype=GRB.BINARY, obj=1.0, name="x_{0}_{1}".format(i, j))

    model.update()

    for i in range(num_participants):
        model.addConstr(
            gp.quicksum(x[i, j] for j in range(num_cars) if (i, j) in x) <= 1,
            name="participant_{0}".format(i),
        )

    for j in range(num_cars):
        model.addConstr(
            gp.quicksum(x[i, j] for i in range(num_participants) if (i, j) in x) <= 1,
            name="car_{0}".format(j),
        )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    if model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    return {"objective": None, "status": "status_{0}".format(model.Status)}