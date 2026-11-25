import gurobipy as gp
from gurobipy import GRB

def solve(params):
    availability = params["availability"]
    demand = params["demand"]
    capacity = params["capacity"]
    cost = params["cost"]

    # Handle both dict and list formats
    if isinstance(availability, dict):
        aircraft_types = list(availability.keys())
        avail_list = [availability[i] for i in aircraft_types]
    else:
        aircraft_types = [f"aircraft_{i}" for i in range(len(availability))]
        avail_list = list(availability)

    if isinstance(demand, dict):
        routes = list(demand.keys())
        demand_list = [demand[j] for j in routes]
    else:
        routes = [f"route_{j}" for j in range(len(demand))]
        demand_list = list(demand)

    n_aircraft = len(aircraft_types)
    n_routes = len(routes)

    # Normalize capacity and cost to indexed access
    def get_val(matrix, i, j):
        ai = aircraft_types[i]
        rj = routes[j]
        if isinstance(matrix, dict):
            row = matrix[ai]
            if isinstance(row, dict):
                return row[rj]
            else:
                return row[j]
        else:
            row = matrix[i]
            if isinstance(row, dict):
                return row[rj]
            else:
                return row[j]

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Decision variables: x[i][j] = number of aircraft type i assigned to route j
    x = {}
    for i in range(n_aircraft):
        for j in range(n_routes):
            x[i, j] = model.addVar(vtype=GRB.INTEGER, lb=0, name=f"x_{i}_{j}")

    # Objective: minimize total cost
    model.setObjective(
        gp.quicksum(get_val(cost, i, j) * x[i, j] for i in range(n_aircraft) for j in range(n_routes)),
        GRB.MINIMIZE
    )

    # Availability constraints
    for i in range(n_aircraft):
        model.addConstr(
            gp.quicksum(x[i, j] for j in range(n_routes)) <= avail_list[i],
            name=f"avail_{i}"
        )

    # Demand constraints
    for j in range(n_routes):
        model.addConstr(
            gp.quicksum(get_val(capacity, i, j) * x[i, j] for i in range(n_aircraft)) >= demand_list[j],
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