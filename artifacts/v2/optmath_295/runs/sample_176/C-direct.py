import gurobipy as gp
from gurobipy import GRB

def solve(params):
    availability = params["availability"]
    demand = params["demand"]
    cost = params["cost"]
    capacity = params["capacity"]

    num_aircraft = 9
    num_routes = 7

    model = gp.Model("airline_assignment")

    x = {}
    for i in range(num_aircraft):
        for j in range(num_routes):
            x[i, j] = model.addVar(vtype=GRB.INTEGER, lb=0, name=f"x_{i}_{j}")

    model.update()

    model.setObjective(
        gp.quicksum(cost[i][j] * x[i, j] for i in range(num_aircraft) for j in range(num_routes)),
        GRB.MINIMIZE,
    )

    for i in range(num_aircraft):
        model.addConstr(
            gp.quicksum(x[i, j] for j in range(num_routes)) <= availability[i],
            name=f"availability_{i}",
        )

    for j in range(num_routes):
        model.addConstr(
            gp.quicksum(capacity[i][j] * x[i, j] for i in range(num_aircraft)) >= demand[j],
            name=f"demand_{j}",
        )

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"status_{model.status}"}