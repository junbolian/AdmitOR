import gurobipy as gp
from gurobipy import GRB

def solve(params):
    truck_capacity = params["truck_capacity"]
    shipment_weights = params["shipment_weights"]
    num_trucks = params["num_trucks"]

    num_shipments = len(shipment_weights)
    trucks = range(num_trucks)
    shipments = range(num_shipments)

    model = gp.Model("bin_packing")
    model.setParam("OutputFlag", 0)

    # y[j] = 1 if truck j is used
    y = model.addVars(trucks, vtype=GRB.BINARY, name="y")
    # x[i, j] = 1 if shipment i is assigned to truck j
    x = model.addVars(shipments, trucks, vtype=GRB.BINARY, name="x")

    # Objective: minimize number of trucks used
    model.setObjective(gp.quicksum(y[j] for j in trucks), GRB.MINIMIZE)

    # Each shipment assigned to exactly one truck
    for i in shipments:
        model.addConstr(gp.quicksum(x[i, j] for j in trucks) == 1, name=f"assign_{i}")

    # Capacity constraints
    for j in trucks:
        model.addConstr(
            gp.quicksum(shipment_weights[i] * x[i, j] for i in shipments) <= truck_capacity * y[j],
            name=f"capacity_{j}"
        )

    # If shipment i is on truck j, truck j must be used
    for i in shipments:
        for j in trucks:
            model.addConstr(x[i, j] <= y[j], name=f"link_{i}_{j}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}