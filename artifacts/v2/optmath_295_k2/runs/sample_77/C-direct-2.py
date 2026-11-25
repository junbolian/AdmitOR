import gurobipy as gp
from gurobipy import GRB


def solve(params):
    costs = params["costs"]
    capacities = params["capacities"]
    aircraft_availability = params["aircraft_availability"]
    route_demand = params["route_demand"]

    n_aircraft = 8
    n_routes = 8

    model = gp.Model("aircraft_assignment")
    model.Params.OutputFlag = 0

    # x[i, j] = number of aircraft type i assigned to route j
    x = model.addVars(n_aircraft, n_routes, vtype=GRB.INTEGER, lb=0, name="x")

    # Objective: minimize total operational cost
    model.setObjective(
        gp.quicksum(
            costs[i][j] * x[i, j]
            for i in range(n_aircraft)
            for j in range(n_routes)
        ),
        GRB.MINIMIZE,
    )

    # Constraint: each aircraft type's total assignments do not exceed availability
    for i in range(n_aircraft):
        model.addConstr(
            gp.quicksum(x[i, j] for j in range(n_routes)) <= aircraft_availability[i],
            name=f"availability_{i}",
        )

    # Constraint: combined capacity on each route meets or exceeds demand
    for j in range(n_routes):
        model.addConstr(
            gp.quicksum(
                capacities[i][j] * x[i, j] for i in range(n_aircraft)
            ) >= route_demand[j],
            name=f"demand_{j}",
        )

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": "failed"}