import gurobipy as gp
from gurobipy import GRB


def solve(params):
    opening_costs = params["opening_costs"]      # list of 6
    transport_costs = params["transport_costs"]  # 6 x 8
    demands = params["demands"]                  # list of 8
    capacities = params["capacities"]             # list of 6

    n_centers = len(opening_costs)
    n_stores = len(demands)

    model = gp.Model("facility_location")
    model.Params.OutputFlag = 0

    open_y = model.addVars(n_centers, vtype=GRB.BINARY, name="open_center")
    ship = model.addVars(n_centers, n_stores, vtype=GRB.CONTINUOUS,
                         lb=0, name="ship")

    # Meet demand at each store
    model.addConstrs(
        (gp.quicksum(ship[i, j] for i in range(n_centers)) == demands[j]
         for j in range(n_stores)),
        name="demand")

    # Capacity at each center, only if opened
    model.addConstrs(
        (gp.quicksum(ship[i, j] for j in range(n_stores)) <= capacities[i] * open_y[i]
         for i in range(n_centers)),
        name="capacity")

    # Open enough capacity to cover total demand (valid inequality, helps LP)
    model.addConstr(
        gp.quicksum(capacities[i] * open_y[i] for i in range(n_centers))
        >= sum(demands),
        name="total_capacity")

    obj = (
        gp.quicksum(opening_costs[i] * open_y[i] for i in range(n_centers))
        + gp.quicksum(transport_costs[i][j] * ship[i, j]
                      for i in range(n_centers) for j in range(n_stores))
    )
    model.setObjective(obj, GRB.MINIMIZE)

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    return {"objective": None, "status": f"status_{model.status}"}