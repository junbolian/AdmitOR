import gurobipy as gp
from gurobipy import GRB

def solve(params):
    availability = params["availability"]  # list of length 5
    demand = params["demand"]              # list of length 5
    capacity = params["capacity"]          # 5x5 list [aircraft][route]
    cost = params["cost"]                  # 5x5 list [aircraft][route]

    num_aircraft = len(availability)
    num_routes = len(demand)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # x[i][j] = number of aircraft type i assigned to route j
    x = [[
        model.addVar(vtype=GRB.INTEGER, lb=0, name=f"x_{i}_{j}")
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
            gp.quicksum(x[i][j] for j in range(num_routes)) <= availability[i],
            name=f"avail_{i}"
        )

    # Passenger demand constraints
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
        return {"objective": None, "status": f"status_{model.Status}"}