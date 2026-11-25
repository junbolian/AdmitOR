import gurobipy as gp
from gurobipy import GRB

def solve(params):
    availability = params["availability"]
    demand = params["demand"]
    cost = params["cost"]
    capability = params["capability"]
    num_aircraft_types = params["num_aircraft_types"]
    num_routes = params["num_routes"]

    model = gp.Model("aircraft_assignment")
    model.setParam("OutputFlag", 0)

    # Decision variables: x[i][j] = number of aircraft type i assigned to route j
    x = [
        [
            model.addVar(vtype=GRB.INTEGER, lb=0, name=f"x_{i}_{j}")
            for j in range(num_routes)
        ]
        for i in range(num_aircraft_types)
    ]

    # Objective: minimize total operational cost
    model.setObjective(
        gp.quicksum(
            cost[i][j] * x[i][j]
            for i in range(num_aircraft_types)
            for j in range(num_routes)
        ),
        GRB.MINIMIZE
    )

    # Availability constraints: total aircraft of type i across all routes <= availability[i]
    for i in range(num_aircraft_types):
        model.addConstr(
            gp.quicksum(x[i][j] for j in range(num_routes)) <= availability[i],
            name=f"avail_{i}"
        )

    # Demand constraints: total capability for route j across all aircraft types >= demand[j]
    for j in range(num_routes):
        model.addConstr(
            gp.quicksum(capability[i][j] * x[i][j] for i in range(num_aircraft_types)) >= demand[j],
            name=f"demand_{j}"
        )

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver_status_{status}"}