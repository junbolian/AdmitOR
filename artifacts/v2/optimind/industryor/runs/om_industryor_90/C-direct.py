import gurobipy as gp
from gurobipy import GRB

def solve(params):
    students = params["students"]
    bus_capacity = params["bus_capacity"]
    minibus_capacity = params["minibus_capacity"]
    bus_cost = params["bus_cost"]
    minibus_cost = params["minibus_cost"]
    num_buses_available = params["num_buses_available"]
    num_minibuses_available = params["num_minibuses_available"]
    num_drivers = params["num_drivers"]

    model = gp.Model("school_trip")
    model.setParam("OutputFlag", 0)

    # Decision variables: number of buses and minibuses to rent
    x = model.addVar(lb=0, ub=num_buses_available, vtype=GRB.INTEGER, name="buses")
    y = model.addVar(lb=0, ub=num_minibuses_available, vtype=GRB.INTEGER, name="minibuses")

    # Objective: minimize total rental cost
    model.setObjective(bus_cost * x + minibus_cost * y, GRB.MINIMIZE)

    # Constraints
    # Enough seats for all students
    model.addConstr(bus_capacity * x + minibus_capacity * y >= students, name="capacity")

    # Cannot exceed available drivers (each vehicle needs one driver)
    model.addConstr(x + y <= num_drivers, name="drivers")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}