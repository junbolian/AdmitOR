import gurobipy as gp
from gurobipy import GRB

def solve(params):
    availability = params["availability"]
    demand = params["demand"]
    capacity = params["capacity"]
    cost = params["cost"]

    # Handle dict or list for availability
    if isinstance(availability, dict):
        aircraft_keys = sorted(availability.keys(), key=lambda k: int(k.split("_")[1]))
        avail_list = [availability[k] for k in aircraft_keys]
    else:
        avail_list = list(availability)

    # Handle dict or list for demand
    if isinstance(demand, dict):
        route_keys = sorted(demand.keys(), key=lambda k: int(k.split("_")[1]))
        demand_list = [demand[k] for k in route_keys]
    else:
        demand_list = list(demand)

    num_aircraft = len(avail_list)
    num_routes = len(demand_list)

    # Handle capacity: could be dict of dicts, list of lists, or list of dicts
    cap = []
    for i in range(num_aircraft):
        row = []
        if isinstance(capacity, dict):
            ak = aircraft_keys[i]
            entry = capacity[ak]
        else:
            entry = capacity[i]

        for j in range(num_routes):
            if isinstance(entry, dict):
                rk = route_keys[j]
                row.append(entry[rk])
            else:
                row.append(entry[j])
        cap.append(row)

    # Handle cost: could be dict of dicts, list of lists, or list of dicts
    cst = []
    for i in range(num_aircraft):
        row = []
        if isinstance(cost, dict):
            ak = aircraft_keys[i]
            entry = cost[ak]
        else:
            entry = cost[i]

        for j in range(num_routes):
            if isinstance(entry, dict):
                rk = route_keys[j]
                row.append(entry[rk])
            else:
                row.append(entry[j])
        cst.append(row)

    model = gp.Model("aircraft_assignment")
    model.setParam("OutputFlag", 0)

    # Decision variables: x[i, j] = number of aircraft type i assigned to route j
    x = {}
    for i in range(num_aircraft):
        for j in range(num_routes):
            x[i, j] = model.addVar(lb=0, vtype=GRB.INTEGER, name=f"x_{i}_{j}")

    # Objective: minimize total cost
    model.setObjective(
        gp.quicksum(cst[i][j] * x[i, j] for i in range(num_aircraft) for j in range(num_routes)),
        GRB.MINIMIZE
    )

    # Availability constraints
    for i in range(num_aircraft):
        model.addConstr(
            gp.quicksum(x[i, j] for j in range(num_routes)) <= avail_list[i],
            name=f"avail_{i}"
        )

    # Demand constraints
    for j in range(num_routes):
        model.addConstr(
            gp.quicksum(cap[i][j] * x[i, j] for i in range(num_aircraft)) >= demand_list[j],
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