import gurobipy as gp
from gurobipy import GRB

def solve(params):
    ref_cap_A = params["refrigerated_capacity_A"]
    nonref_cap_A = params["nonrefrigerated_capacity_A"]
    total_cap_B = params["total_capacity_B"]
    ref_demand = params["refrigerated_demand"]
    nonref_demand = params["nonrefrigerated_demand"]
    cost_A = params["cost_per_km_A"]
    cost_B = params["cost_per_km_B"]

    # Type B splits total capacity equally between refrigerated and non-refrigerated
    ref_cap_B = total_cap_B / 2.0
    nonref_cap_B = total_cap_B / 2.0

    model = gp.Model("truck_rental")
    model.setParam("OutputFlag", 0)

    # Decision variables: number of each truck type (integer)
    x_A = model.addVar(vtype=GRB.INTEGER, lb=0, name="x_A")
    x_B = model.addVar(vtype=GRB.INTEGER, lb=0, name="x_B")

    # Objective: minimize total cost per km
    model.setObjective(cost_A * x_A + cost_B * x_B, GRB.MINIMIZE)

    # Constraints: meet refrigerated and non-refrigerated demands
    model.addConstr(ref_cap_A * x_A + ref_cap_B * x_B >= ref_demand, name="ref_demand")
    model.addConstr(nonref_cap_A * x_A + nonref_cap_B * x_B >= nonref_demand, name="nonref_demand")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}