import gurobipy as gp
from gurobipy import GRB

def solve(params):
    truck_capacity = params["truck_capacity"]
    shipment_weights = params["shipment_weights"]

    n = len(shipment_weights)
    # Upper bound on trucks needed: one per shipment
    max_trucks = n

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # x[i][j] = 1 if shipment i is assigned to truck j
    x = [[model.addVar(vtype=GRB.BINARY) for j in range(max_trucks)] for i in range(n)]
    # y[j] = 1 if truck j is used
    y = [model.addVar(vtype=GRB.BINARY) for j in range(max_trucks)]

    # Objective: minimize number of trucks used
    model.setObjective(gp.quicksum(y[j] for j in range(max_trucks)), GRB.MINIMIZE)

    # Each shipment assigned to exactly one truck
    for i in range(n):
        model.addConstr(gp.quicksum(x[i][j] for j in range(max_trucks)) == 1)

    # Capacity constraints
    for j in range(max_trucks):
        model.addConstr(
            gp.quicksum(shipment_weights[i] * x[i][j] for i in range(n)) <= truck_capacity * y[j]
        )

    # Symmetry breaking: truck j can only be used if truck j-1 is used
    for j in range(1, max_trucks):
        model.addConstr(y[j] <= y[j - 1])

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"solver_status_{model.Status}"}