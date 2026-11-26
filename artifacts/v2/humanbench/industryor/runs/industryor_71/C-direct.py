import gurobipy as gp
from gurobipy import GRB

def solve(params):
    profit_truck = params["profit_truck"]
    profit_plane = params["profit_plane"]
    profit_boat = params["profit_boat"]
    profit_train = params["profit_train"]

    wood_available = params["wood_available"]
    wood_truck = params["wood_truck"]
    wood_plane = params["wood_plane"]
    wood_boat = params["wood_boat"]
    wood_train = params["wood_train"]

    steel_available = params["steel_available"]
    steel_truck = params["steel_truck"]
    steel_plane = params["steel_plane"]
    steel_boat = params["steel_boat"]
    steel_train = params["steel_train"]

    model = gp.Model("haus_toys")
    model.setParam("OutputFlag", 0)

    # Continuous production quantities
    truck = model.addVar(lb=0, vtype=GRB.CONTINUOUS, name="truck")
    plane = model.addVar(lb=0, vtype=GRB.CONTINUOUS, name="plane")
    boat  = model.addVar(lb=0, vtype=GRB.CONTINUOUS, name="boat")
    train = model.addVar(lb=0, vtype=GRB.CONTINUOUS, name="train")

    # Binary indicators: 1 if product type is manufactured
    y_truck = model.addVar(vtype=GRB.BINARY, name="y_truck")
    y_plane = model.addVar(vtype=GRB.BINARY, name="y_plane")
    y_boat  = model.addVar(vtype=GRB.BINARY, name="y_boat")
    y_train = model.addVar(vtype=GRB.BINARY, name="y_train")

    # Big-M: upper bounds on production quantities
    # Use resource-based bounds
    M_truck = min(wood_available / wood_truck, steel_available / steel_truck)
    M_plane = min(wood_available / wood_plane, steel_available / steel_plane)
    M_boat  = min(wood_available / wood_boat,  steel_available / steel_boat)
    M_train = min(wood_available / wood_train, steel_available / steel_train)

    # Link quantities to binary indicators
    model.addConstr(truck <= M_truck * y_truck, name="link_truck")
    model.addConstr(plane <= M_plane * y_plane, name="link_plane")
    model.addConstr(boat  <= M_boat  * y_boat,  name="link_boat")
    model.addConstr(train <= M_train * y_train, name="link_train")

    # If y=1, at least some production (at least 1 unit)
    model.addConstr(truck >= y_truck, name="min_truck")
    model.addConstr(plane >= y_plane, name="min_plane")
    model.addConstr(boat  >= y_boat,  name="min_boat")
    model.addConstr(train >= y_train, name="min_train")

    # Resource constraints
    model.addConstr(
        wood_truck * truck + wood_plane * plane + wood_boat * boat + wood_train * train <= wood_available,
        name="wood"
    )
    model.addConstr(
        steel_truck * truck + steel_plane * plane + steel_boat * boat + steel_train * train <= steel_available,
        name="steel"
    )

    # If trucks are manufactured, trains are not: y_truck + y_train <= 1
    model.addConstr(y_truck + y_train <= 1, name="truck_no_train")

    # If boats are manufactured, planes are also manufactured: y_boat <= y_plane
    model.addConstr(y_boat <= y_plane, name="boat_implies_plane")

    # Number of boats cannot exceed number of trains: boat <= train
    model.addConstr(boat <= train, name="boat_le_train")

    # Objective: maximize profit
    model.setObjective(
        profit_truck * truck + profit_plane * plane + profit_boat * boat + profit_train * train,
        GRB.MAXIMIZE
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