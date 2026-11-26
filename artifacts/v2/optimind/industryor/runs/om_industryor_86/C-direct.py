import gurobipy as gp
from gurobipy import GRB

def solve(params):
    machine1_time_liquid = params["machine1_time_liquid"]
    machine2_time_liquid = params["machine2_time_liquid"]
    machine1_time_solid  = params["machine1_time_solid"]
    machine2_time_solid  = params["machine2_time_solid"]
    initial_inventory_liquid = params["initial_inventory_liquid"]
    initial_inventory_solid  = params["initial_inventory_solid"]
    machine1_capacity_hours  = params["machine1_capacity_hours"]
    machine2_capacity_hours  = params["machine2_capacity_hours"]
    demand_liquid = params["demand_liquid"]
    demand_solid  = params["demand_solid"]

    machine1_capacity_minutes = machine1_capacity_hours * 60
    machine2_capacity_minutes = machine2_capacity_hours * 60

    model = gp.Model("fertilizer")
    model.setParam("OutputFlag", 0)

    # Decision variables: units produced this week
    x_liquid = model.addVar(vtype=GRB.INTEGER, lb=0, name="x_liquid")
    x_solid  = model.addVar(vtype=GRB.INTEGER, lb=0, name="x_solid")

    # End-of-week inventory
    inv_liquid = model.addVar(vtype=GRB.INTEGER, lb=0, name="inv_liquid")
    inv_solid  = model.addVar(vtype=GRB.INTEGER, lb=0, name="inv_solid")

    # Inventory balance
    model.addConstr(inv_liquid == initial_inventory_liquid + x_liquid - demand_liquid,
                    name="balance_liquid")
    model.addConstr(inv_solid  == initial_inventory_solid  + x_solid  - demand_solid,
                    name="balance_solid")

    # Machine capacity constraints (in minutes)
    model.addConstr(
        machine1_time_liquid * x_liquid + machine1_time_solid * x_solid <= machine1_capacity_minutes,
        name="machine1_capacity"
    )
    model.addConstr(
        machine2_time_liquid * x_liquid + machine2_time_solid * x_solid <= machine2_capacity_minutes,
        name="machine2_capacity"
    )

    # Objective: maximize total ending inventory
    model.setObjective(inv_liquid + inv_solid, GRB.MAXIMIZE)

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