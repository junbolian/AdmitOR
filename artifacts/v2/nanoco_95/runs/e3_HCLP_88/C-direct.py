import gurobipy as gp
from gurobipy import GRB
import math

def solve(params):
    installation_cost = params["installation_cost"]
    client_x = params["client_x"]
    client_y = params["client_y"]
    facility_x = params["facility_x"]
    facility_y = params["facility_y"]
    demand = params["demand"]
    distance_matrix = params["distance_matrix"]
    R1 = params["basic_radius_R1"]
    R2 = params["premium_radius_R2"]
    premium_bonus = params["premium_bonus"]

    num_clients = 21
    num_facilities = 15
    clients = range(num_clients)
    facilities = range(num_facilities)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # y[j] = 1 if facility j is installed
    y = model.addVars(facilities, vtype=GRB.BINARY, name="y")

    # p[i][j] = 1 if client i receives premium service from facility j
    p = model.addVars(clients, facilities, vtype=GRB.BINARY, name="p")

    # Objective: minimize total installation cost minus premium bonus revenue
    model.setObjective(
        gp.quicksum(installation_cost[j] * y[j] for j in facilities)
        - gp.quicksum(premium_bonus[i] * p[i, j] for i in clients for j in facilities),
        GRB.MINIMIZE
    )

    # Coverage constraint: every client must be covered within R1 by at least one installed facility
    for i in clients:
        eligible = [j for j in facilities if distance_matrix[i][j] <= R1]
        if not eligible:
            return {"objective": None, "status": "infeasible: client cannot be covered"}
        model.addConstr(
            gp.quicksum(y[j] for j in eligible) >= 1,
            name=f"cover_{i}"
        )

    # Premium service: p[i,j] can be 1 only if facility j is installed and distance <= R2
    for i in clients:
        for j in facilities:
            if distance_matrix[i][j] <= R2:
                model.addConstr(p[i, j] <= y[j], name=f"prem_link_{i}_{j}")
            else:
                model.addConstr(p[i, j] == 0, name=f"prem_zero_{i}_{j}")

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver status {status}"}