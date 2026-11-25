import gurobipy as gp
from gurobipy import GRB

def solve(params):
    availability = params["availability"]  # list of length n_aircraft
    demand = params["demand"]              # list of length n_routes
    cost = params["cost"]                  # n_aircraft x n_routes
    capacity = params["capacity"]          # n_aircraft x n_routes

    n_aircraft = len(availability)
    n_routes = len(demand)

    model = gp.Model("aircraft_assignment")
    model.setParam("OutputFlag", 0)

    # Decision variables: x[i][j] = number of aircraft type i assigned to route j
    x = [[model.addVar(vtype=GRB.INTEGER, lb=0, name=f"x_{i}_{j}")
          for j in range(n_routes)]
         for i in range(n_aircraft)]

    # Objective: minimize total cost
    model.setObjective(
        gp.quicksum(cost[i][j] * x[i][j]
                    for i in range(n_aircraft)
                    for j in range(n_routes)),
        GRB.MINIMIZE
    )

    # Availability constraints: total aircraft of type i across all routes <= availability[i]
    for i in range(n_aircraft):
        model.addConstr(
            gp.quicksum(x[i][j] for j in range(n_routes)) <= availability[i],
            name=f"avail_{i}"
        )

    # Demand constraints: total capacity on route j >= demand[j]
    for j in range(n_routes):
        model.addConstr(
            gp.quicksum(capacity[i][j] * x[i][j] for i in range(n_aircraft)) >= demand[j],
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