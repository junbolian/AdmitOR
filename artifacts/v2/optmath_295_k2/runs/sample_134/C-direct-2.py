import gurobipy as gp
from gurobipy import GRB


def solve(params):
    availability = params["availability"]
    demand = params["demand"]
    cost = params["cost"]
    capability = params["capability"]
    num_aircraft_types = params["num_aircraft_types"]
    num_routes = params["num_routes"]

    model = gp.Model("airline_assignment")

    x = {}
    for i in range(num_aircraft_types):
        for j in range(num_routes):
            x[i, j] = model.addVar(vtype=GRB.INTEGER, lb=0, name=f"x_{i}_{j}")

    model.setObjective(
        gp.quicksum(
            cost[i][j] * x[i, j]
            for i in range(num_aircraft_types)
            for j in range(num_routes)
        ),
        GRB.MINIMIZE,
    )

    for i in range(num_aircraft_types):
        model.addConstr(
            gp.quicksum(x[i, j] for j in range(num_routes)) <= availability[i],
            name=f"avail_{i}",
        )

    for j in range(num_routes):
        model.addConstr(
            gp.quicksum(
                capability[i][j] * x[i, j] for i in range(num_aircraft_types)
            )
            >= demand[j],
            name=f"demand_{j}",
        )

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    else:
        return {"objective": None, "status": f"status_{model.status}"}