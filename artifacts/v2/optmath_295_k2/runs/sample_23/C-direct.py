import gurobipy as gp
from gurobipy import GRB


def solve(params):
    availability = params["availability"]
    demand = params["demand"]
    capability = params["capability"]
    cost = params["cost"]

    n_aircraft = len(availability)
    n_routes = len(demand)

    model = gp.Model("aircraft_assignment")
    model.setParam("OutputFlag", 0)

    x = model.addVars(n_aircraft, n_routes, vtype=GRB.INTEGER, lb=0, name="x")

    model.setObjective(
        gp.quicksum(
            cost[i][j] * x[i, j]
            for i in range(n_aircraft)
            for j in range(n_routes)
        ),
        GRB.MINIMIZE,
    )

    for i in range(n_aircraft):
        model.addConstr(
            gp.quicksum(x[i, j] for j in range(n_routes)) <= availability[i],
            name=f"availability_{i}",
        )

    for j in range(n_routes):
        model.addConstr(
            gp.quicksum(
                capability[i][j] * x[i, j] for i in range(n_aircraft)
            ) >= demand[j],
            name=f"demand_{j}",
        )

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": "failed"}