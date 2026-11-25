import gurobipy as gp
from gurobipy import GRB

def solve(params):
    costs = params["costs"]
    capacities = params["capacities"]
    aircraft_availability = params["aircraft_availability"]
    route_demand = params["route_demand"]

    n_aircraft = 8
    n_routes = 8

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Binary assignment variables: x[i][j] = 1 if aircraft i is assigned to route j
    x = [[model.addVar(vtype=GRB.BINARY, name=f"x_{i}_{j}")
          for j in range(n_routes)]
         for i in range(n_aircraft)]

    # Objective: minimize total cost
    model.setObjective(
        gp.quicksum(costs[i][j] * x[i][j]
                    for i in range(n_aircraft)
                    for j in range(n_routes)),
        GRB.MINIMIZE
    )

    # Aircraft availability constraints
    for i in range(n_aircraft):
        model.addConstr(
            gp.quicksum(x[i][j] for j in range(n_routes)) <= aircraft_availability[i],
            name=f"avail_{i}"
        )

    # Route demand constraints
    for j in range(n_routes):
        model.addConstr(
            gp.quicksum(capacities[i][j] * x[i][j] for i in range(n_aircraft)) >= route_demand[j],
            name=f"demand_{j}"
        )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}