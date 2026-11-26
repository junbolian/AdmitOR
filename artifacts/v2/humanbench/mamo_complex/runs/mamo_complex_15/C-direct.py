import gurobipy as gp
from gurobipy import GRB


def solve(params):
    opening_costs = params["opening_costs"]
    transport_costs = params["transport_costs"]
    demands = params["demands"]
    capacities = params["capacities"]
    num_centers = int(params["num_centers"])
    num_stores = int(params["num_stores"])

    centers = range(num_centers)
    stores = range(num_stores)

    model = gp.Model("facility_location")
    model.Params.OutputFlag = 0

    y = model.addVars(centers, vtype=GRB.BINARY, name="open")
    x = model.addVars(centers, stores, lb=0.0, vtype=GRB.CONTINUOUS, name="ship")

    model.setObjective(
        gp.quicksum(opening_costs[i] * y[i] for i in centers)
        + gp.quicksum(transport_costs[i][j] * x[i, j] for i in centers for j in stores),
        GRB.MINIMIZE,
    )

    for j in stores:
        model.addConstr(gp.quicksum(x[i, j] for i in centers) >= demands[j], name=f"demand_{j}")

    for i in centers:
        model.addConstr(
            gp.quicksum(x[i, j] for j in stores) <= capacities[i] * y[i],
            name=f"cap_{i}",
        )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    if model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    return {"objective": None, "status": f"status_{model.Status}"}