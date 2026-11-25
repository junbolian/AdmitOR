import gurobipy as gp
from gurobipy import GRB


def solve(params):
    flammability_capacity_per_vehicle = params["flammability_capacity_per_vehicle"]
    toxicity_capacity_per_vehicle = params["toxicity_capacity_per_vehicle"]
    flammability_demand = params["flammability_demand"]
    toxicity_demand = params["toxicity_demand"]

    n_shipments = len(flammability_demand)
    n_vehicles = n_shipments  # upper bound: one vehicle per shipment

    model = gp.Model("hazmat_transport")
    model.setParam("OutputFlag", 0)

    # x[i, j] = 1 if shipment i is assigned to vehicle j
    x = model.addVars(n_shipments, n_vehicles, vtype=GRB.BINARY, name="x")
    # y[j] = 1 if vehicle j is activated
    y = model.addVars(n_vehicles, vtype=GRB.BINARY, name="y")

    # Each shipment must be assigned to exactly one vehicle
    for i in range(n_shipments):
        model.addConstr(gp.quicksum(x[i, j] for j in range(n_vehicles)) == 1)

    # Per-vehicle capacity constraints on flammability and toxicity
    for j in range(n_vehicles):
        model.addConstr(
            gp.quicksum(flammability_demand[i] * x[i, j] for i in range(n_shipments))
            <= flammability_capacity_per_vehicle * y[j]
        )
        model.addConstr(
            gp.quicksum(toxicity_demand[i] * x[i, j] for i in range(n_shipments))
            <= toxicity_capacity_per_vehicle * y[j]
        )

    # Symmetry breaking: activate vehicles in decreasing index order
    for j in range(n_vehicles - 1):
        model.addConstr(y[j] >= y[j + 1])

    # Minimize number of activated vehicles
    model.setObjective(gp.quicksum(y[j] for j in range(n_vehicles)), GRB.MINIMIZE)

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    else:
        return {"objective": None, "status": "failed"}