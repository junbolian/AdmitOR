import gurobipy as gp
from gurobipy import GRB
import math

def solve(params):
    facility_installation_cost = params["facility_installation_cost"]
    client_demand = params["client_demand"]
    client_premium_bonus = params["client_premium_bonus"]
    R1 = params["basic_coverage_radius_R1"]
    R2 = params["premium_coverage_radius_R2"]
    household_coordinates = params["household_coordinates"]
    facility_coordinates = params["facility_coordinates"]
    distance_matrix = params["distance_matrix"]

    num_clients = len(client_demand)
    num_facilities = len(facility_installation_cost)

    clients = range(num_clients)
    facilities = range(num_facilities)

    model = gp.Model("rural_broadband")
    model.setParam("OutputFlag", 0)

    # y[j] = 1 if facility j is installed
    y = model.addVars(facilities, vtype=GRB.BINARY, name="y")

    # p[i] = 1 if client i receives premium service (within R2 of at least one installed facility)
    p = model.addVars(clients, vtype=GRB.BINARY, name="p")

    # Objective: minimize total installation cost minus total premium bonus
    model.setObjective(
        gp.quicksum(facility_installation_cost[j] * y[j] for j in facilities)
        - gp.quicksum(client_premium_bonus[i] * p[i] for i in clients),
        GRB.MINIMIZE
    )

    # Hard constraint: every client must be within R1 of at least one installed facility
    for i in clients:
        basic_facilities = [j for j in facilities if distance_matrix[i][j] <= R1]
        if not basic_facilities:
            return {"objective": None, "status": "infeasible: client has no facility within R1"}
        model.addConstr(
            gp.quicksum(y[j] for j in basic_facilities) >= 1,
            name=f"basic_coverage_{i}"
        )

    # Premium service: p[i] can be 1 only if at least one installed facility is within R2
    for i in clients:
        premium_facilities = [j for j in facilities if distance_matrix[i][j] <= R2]
        if not premium_facilities:
            # Client cannot get premium service; force p[i] = 0 (default is 0 anyway)
            model.addConstr(p[i] == 0, name=f"no_premium_{i}")
        else:
            # p[i] <= sum of y[j] for j in premium_facilities (can't claim premium if none installed)
            model.addConstr(
                p[i] <= gp.quicksum(y[j] for j in premium_facilities),
                name=f"premium_coverage_{i}"
            )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver status {model.Status}"}