import gurobipy as gp
from gurobipy import GRB

def solve(params):
    availability = params["availability"]
    demand = params["demand"]
    cost = params["cost"]
    capacity = params["capacity"]

    num_aircraft = 9
    num_routes = 7

    model = gp.Model("aircraft_assignment")
    model.setParam("OutputFlag", 0)

    # Decision variables: x[i][j] = number of aircraft type i assigned to route j
    x = [[model.addVar(vtype=GRB.INTEGER, lb=0, name=f"x_{i}_{j}")
          for j in range(num_routes)]
         for i in range(num_aircraft)]

    # Objective: minimize total operational cost
    model.setObjective(
        gp.quicksum(cost[i][j] * x[i][j]
                    for i in range(num_aircraft)
                    for j in range(num_routes)),
        GRB.MINIMIZE
    )

    # Availability constraints: total assigned of each aircraft type <= availability
    for i in range(num_aircraft):
        model.addConstr(
            gp.quicksum(x[i][j] for j in range(num_routes)) <= availability[i],
            name=f"avail_{i}"
        )

    # Demand constraints: total capacity on each route >= demand
    for j in range(num_routes):
        model.addConstr(
            gp.quicksum(capacity[i][j] * x[i][j] for i in range(num_aircraft)) >= demand[j],
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
        return {"objective": None, "status": f"solver_status_{model.Status}"}