import gurobipy as gp
from gurobipy import GRB

def solve(params):
    aircraft_availability = params["aircraft_availability"]
    route_demand = params["route_demand"]
    capacity = params["capacity"]
    cost = params["cost"]

    num_aircraft = 6
    num_routes = 3

    model = gp.Model("aircraft_allocation")
    model.setParam("OutputFlag", 0)

    # Decision variables: x[i][j] = number of aircraft type i assigned to route j
    x = [[model.addVar(vtype=GRB.INTEGER, lb=0, name=f"x_{i}_{j}")
          for j in range(num_routes)]
         for i in range(num_aircraft)]

    # Objective: minimize total cost
    model.setObjective(
        gp.quicksum(cost[i][j] * x[i][j]
                    for i in range(num_aircraft)
                    for j in range(num_routes)),
        GRB.MINIMIZE
    )

    # Aircraft availability constraints
    for i in range(num_aircraft):
        model.addConstr(
            gp.quicksum(x[i][j] for j in range(num_routes)) <= aircraft_availability[i],
            name=f"avail_{i}"
        )

    # Route demand constraints
    for j in range(num_routes):
        model.addConstr(
            gp.quicksum(capacity[i][j] * x[i][j] for i in range(num_aircraft)) >= route_demand[j],
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