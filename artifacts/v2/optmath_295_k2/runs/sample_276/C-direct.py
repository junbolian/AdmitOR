import gurobipy as gp
from gurobipy import GRB

def solve(params):
    availability = params["availability"]
    demand = params["demand"]
    capacity = params["capacity"]
    cost = params["cost"]

    # Handle both list and dict formats for availability and demand
    if isinstance(availability, list):
        aircraft_types = list(range(len(availability)))
        avail_dict = {i: availability[i] for i in aircraft_types}
    else:
        aircraft_types = list(availability.keys())
        avail_dict = availability

    if isinstance(demand, list):
        routes = list(range(len(demand)))
        demand_dict = {j: demand[j] for j in routes}
    else:
        routes = list(demand.keys())
        demand_dict = demand

    # Normalize capacity and cost to indexed access
    # capacity[i][j]: if keys are strings like "aircraft_0", map accordingly
    def get_val(matrix, i, j):
        # Try direct index first, then string key
        if isinstance(matrix, list):
            row = matrix[i] if isinstance(i, int) else matrix[int(i.split("_")[1])]
            if isinstance(row, list):
                return row[j] if isinstance(j, int) else row[int(j.split("_")[1])]
            else:
                return row[j]
        else:
            row = matrix[i]
            return row[j]

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Decision variables: number of aircraft type i assigned to route j
    x = {}
    for i in aircraft_types:
        for j in routes:
            x[i, j] = model.addVar(vtype=GRB.INTEGER, lb=0, name=f"x_{i}_{j}")

    # Objective: minimize total cost
    model.setObjective(
        gp.quicksum(get_val(cost, i, j) * x[i, j] for i in aircraft_types for j in routes),
        GRB.MINIMIZE
    )

    # Availability constraints
    for i in aircraft_types:
        model.addConstr(
            gp.quicksum(x[i, j] for j in routes) <= avail_dict[i],
            name=f"avail_{i}"
        )

    # Demand constraints
    for j in routes:
        model.addConstr(
            gp.quicksum(get_val(capacity, i, j) * x[i, j] for i in aircraft_types) >= demand_dict[j],
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