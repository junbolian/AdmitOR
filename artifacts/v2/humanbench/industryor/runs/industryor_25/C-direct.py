import gurobipy as gp
from gurobipy import GRB

def solve(params):
    supply_A_lower = params["supply_A_lower"]
    supply_B_lower = params["supply_B_lower"]
    demand_1 = params["demand_1"]
    demand_2 = params["demand_2"]
    demand_3 = params["demand_3"]
    dist_A1 = params["dist_A1"]
    dist_A2 = params["dist_A2"]
    dist_A3 = params["dist_A3"]
    dist_B1 = params["dist_B1"]
    dist_B2 = params["dist_B2"]
    dist_B3 = params["dist_B3"]

    model = gp.Model("coal_transport")
    model.setParam("OutputFlag", 0)

    # Decision variables: tons shipped from mine i to area j
    xA1 = model.addVar(lb=0, name="xA1")
    xA2 = model.addVar(lb=0, name="xA2")
    xA3 = model.addVar(lb=0, name="xA3")
    xB1 = model.addVar(lb=0, name="xB1")
    xB2 = model.addVar(lb=0, name="xB2")
    xB3 = model.addVar(lb=0, name="xB3")

    # Objective: minimize total ton-kilometers
    model.setObjective(
        dist_A1 * xA1 + dist_A2 * xA2 + dist_A3 * xA3 +
        dist_B1 * xB1 + dist_B2 * xB2 + dist_B3 * xB3,
        GRB.MINIMIZE
    )

    # Supply constraints (mines supply at least their minimum)
    model.addConstr(xA1 + xA2 + xA3 >= supply_A_lower, name="supply_A")
    model.addConstr(xB1 + xB2 + xB3 >= supply_B_lower, name="supply_B")

    # Demand constraints (each area receives exactly its requirement)
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