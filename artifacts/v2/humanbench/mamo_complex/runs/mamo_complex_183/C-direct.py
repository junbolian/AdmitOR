import gurobipy as gp
from gurobipy import GRB


def solve(params):
    opening_costs = params["opening_costs"]
    transport_costs = params["transport_costs"]
    demands = params["demands"]
    capacities = params["capacities"]

    n_centers = len(capacities)
    n_stores = len(demands)

    model = gp.Model("supply_chain")
    model.Params.OutputFlag = 0

    # Binary: open distribution center i
    open_center = model.addVars(n_centers, vtype=GRB.BINARY, name="open")
    # Units shipped from center i to store j
    ship = model.addVars(n_centers, n_stores, vtype=GRB.CONTINUOUS, name="ship")

    # Each store's demand must be met
    model.addConstrs(
        (gp.quicksum(ship[i, j] for i in range(n_centers)) == demands[j] for j in range(n_stores)),
        name="demand",
    )

    # Center capacity, enforced only if open
    model.addConstrs(
        (gp.quicksum(ship[i, j] for j in range(n_stores)) <= capacities[i] * open_center[i]
         for i in range(n_centers)),
        name="capacity",
    )

    # Total opening cost
    opening_total = gp.quicksum(
        opening_costs[i] * open_center[i] for i in range(n_centers)
    )
    # Total transportation cost
    transport_total = gp.quicksum(
        transport_costs[i][j] * ship[i, j]
        for i in range(n_centers)
        for j in range(n_stores)
    )

    model.setObjective(opening_total + transport_total, GRB.MINIMIZE)

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    return {"objective": None, "status": "no_optimal_solution"}