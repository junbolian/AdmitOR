import gurobipy as gp
from gurobipy import GRB


def solve(params):
    aircraft_availability = params["aircraft_availability"]
    route_demand = params["route_demand"]
    cost_matrix = params["cost_matrix"]
    capacity_matrix = params["capacity_matrix"]

    n_aircraft = 8
    n_routes = 8

    model = gp.Model("airline_assignment")
    model.Params.OutputFlag = 0

    x = model.addVars(n_aircraft, n_routes, vtype=GRB.BINARY, name="x")

    model.setObjective(
        gp.quicksum(
            cost_matrix[i][j] * x[i, j]
            for i in range(n_aircraft)
            for j in range(n_routes)
        ),
        GRB.MINIMIZE,
    )

    for i in range(n_aircraft):
        model.addConstr(
            gp.quicksum(x[i, j] for j in range(n_routes)) <= aircraft_availability[i],
            name=f"availability_{i}",
        )

    for j in range(n_routes):
        model.addConstr(
            gp.quicksum(
                capacity_matrix[i][j] * x[i, j] for i in range(n_aircraft)
            ) >= route_demand[j],
            name=f"demand_{j}",
        )

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    if model.status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    return {"objective": None, "status": "failed"}