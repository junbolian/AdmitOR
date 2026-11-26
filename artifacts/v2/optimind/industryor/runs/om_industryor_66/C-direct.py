import gurobipy as gp
from gurobipy import GRB

def solve(params):
    supply_A_min = params["supply_A_min"]
    supply_B_min = params["supply_B_min"]
    demand_1 = params["demand_1"]
    demand_2 = params["demand_2"]
    demand_3 = params["demand_3"]
    distance_A1 = params["distance_A1"]
    distance_A2 = params["distance_A2"]
    distance_A3 = params["distance_A3"]
    distance_B1 = params["distance_B1"]
    distance_B2 = params["distance_B2"]
    distance_B3 = params["distance_B3"]

    model = gp.Model("coal_distribution")
    model.setParam("OutputFlag", 0)

    # Decision variables: tons shipped from yard i to area j
    xA1 = model.addVar(lb=0, name="xA1")
    xA2 = model.addVar(lb=0, name="xA2")
    xA3 = model.addVar(lb=0, name="xA3")
    xB1 = model.addVar(lb=0, name="xB1")
    xB2 = model.addVar(lb=0, name="xB2")
    xB3 = model.addVar(lb=0, name="xB3")

    # Objective: minimize total ton-kilometers
    model.setObjective(
        distance_A1 * xA1 + distance_A2 * xA2 + distance_A3 * xA3 +
        distance_B1 * xB1 + distance_B2 * xB2 + distance_B3 * xB3,
        GRB.MINIMIZE
    )

    # Supply constraints: each yard ships at least its minimum
    model.addConstr(xA1 + xA2 + xA3 >= supply_A_min, name="supply_A")
    model.addConstr(xB1 + xB2 + xB3 >= supply_B_min, name="supply_B")

    # Demand constraints: each area receives exactly its demand
    model.addConstr(xA1 + xB1 == demand_1, name="demand_1")
    model.addConstr(xA2 + xB2 == demand_2, name="demand_2")
    model.addConstr(xA3 + xB3 == demand_3, name="demand_3")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}