import gurobipy as gp
from gurobipy import GRB

def solve(params):
    availability = params["availability"]  # indexed by aircraft type
    demand = params["demand"]              # indexed by route
    capacity = params["capacity"]          # 2D: capacity[i][j]
    cost_matrix = params["cost"]           # 2D: cost[i][j]

    num_aircraft = 6
    num_routes = 7
    aircraft_types = range(num_aircraft)
    routes = range(num_routes)

    model = gp.Model("aircraft_assignment")
    model.setParam("OutputFlag", 0)

    # Decision variables: x[i][j] = number of aircraft type i assigned to route j
    x = [[model.addVar(vtype=GRB.INTEGER, lb=0, name=f"x_{i}_{j}")
          for j in routes] for i in aircraft_types]

    # Objective: minimize total operational cost
    model.setObjective(
        gp.quicksum(cost_matrix[i][j] * x[i][j] for i in aircraft_types for j in routes),
        GRB.MINIMIZE
    )

    # Availability constraints: total aircraft of type i assigned across all routes <= availability[i]
    for i in aircraft_types:
        model.addConstr(
            gp.quicksum(x[i][j] for j in routes) <= availability[i],
            name=f"avail_{i}"
        )

    # Demand constraints: total capacity on route j from all aircraft >= demand[j]
    for j in routes:
        model.addConstr(
            gp.quicksum(capacity[i][j] * x[i][j] for i in aircraft_types) >= demand[j],
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