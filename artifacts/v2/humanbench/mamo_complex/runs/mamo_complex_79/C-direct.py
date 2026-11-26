import gurobipy as gp
from gurobipy import GRB


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    transport_cost = params["transport_cost"]

    warehouses = [1, 2, 3, 4]
    pairs = [
        (1, 2), (1, 3), (1, 4), (2, 1), (2, 3), (2, 4),
        (3, 1), (3, 2), (3, 4), (4, 1), (4, 2), (4, 3),
    ]

    # Build a dict mapping (i,j) -> cost, handling both list and dict inputs
    if isinstance(transport_cost, dict):
        cost = {pair: transport_cost[pair] for pair in pairs}
    else:
        cost = {pair: transport_cost[idx] for idx, pair in enumerate(pairs)}

    model = gp.Model("food_relocation")
    model.setParam("OutputFlag", 0)

    ship = model.addVars(pairs, lb=0.0, vtype=GRB.CONTINUOUS, name="ship")

    model.setObjective(
        gp.quicksum(cost[(i, j)] * ship[i, j] for (i, j) in pairs),
        GRB.MINIMIZE,
    )

    for w in warehouses:
        inflow = gp.quicksum(ship[i, w] for (i, j) in pairs if j == w)
        outflow = gp.quicksum(ship[w, j] for (i, j) in pairs if i == w)
        model.addConstr(
            supply[w - 1] + inflow - outflow >= demand[w - 1],
            name=f"meet_demand_{w}",
        )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    return {"objective": None, "status": f"status_{model.Status}"}