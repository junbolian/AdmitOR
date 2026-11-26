import gurobipy as gp
from gurobipy import GRB

def solve(params):
    demand_A = params["demand_A"]
    demand_B = params["demand_B"]
    demand_C = params["demand_C"]
    supply_A_per_truck = params["supply_A_per_truck"]
    supply_B_per_truck = params["supply_B_per_truck"]
    supply_C_per_truck_A = params["supply_C_per_truck_A"]
    supply_A_per_truck_B = params["supply_A_per_truck_B"]
    supply_B_per_truck_B = params["supply_B_per_truck_B"]
    supply_C_per_truck_B = params["supply_C_per_truck_B"]
    cost_per_truck_A = params["cost_per_truck_A"]
    cost_per_truck_B = params["cost_per_truck_B"]

    model = gp.Model("freight_optimization")
    model.setParam("OutputFlag", 0)

    # Decision variables: number of trucks from each warehouse (integer)
    x = model.addVar(vtype=GRB.INTEGER, lb=0, name="trucks_A")
    y = model.addVar(vtype=GRB.INTEGER, lb=0, name="trucks_B")

    # Objective: minimize total freight cost
    model.setObjective(cost_per_truck_A * x + cost_per_truck_B * y, GRB.MINIMIZE)

    # Constraints: meet demand for each material
    model.addConstr(supply_A_per_truck * x + supply_A_per_truck_B * y >= demand_A, name="demand_A_con")
    model.addConstr(supply_B_per_truck * x + supply_B_per_truck_B * y >= demand_B, name="demand_B_con")
    model.addConstr(supply_C_per_truck_A * x + supply_C_per_truck_B * y >= demand_C, name="demand_C_con")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}