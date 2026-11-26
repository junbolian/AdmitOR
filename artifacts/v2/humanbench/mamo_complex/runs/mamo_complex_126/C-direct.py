import gurobipy as gp
from gurobipy import GRB


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    transport_cost = params["transport_cost"]

    n = len(supply)
    regions = range(n)

    model = gp.Model("medical_supply_distribution")
    model.Params.OutputFlag = 0

    x = model.addVars(n, n, lb=0.0, name="x")

    # Each region: what it holds after transfers must cover its demand
    for i in regions:
        model.addConstr(
            supply[i] + gp.quicksum(x[j, i] for j in regions)
            - gp.quicksum(x[i, j] for j in regions) >= demand[i]
        )

    # Cannot ship more than available (implied by the above plus nonneg, kept for tightness)
    for i in regions:
        model.addConstr(
            gp.quicksum(x[i, j] for j in regions) <= supply[i]
        )

    model.setObjective(
        gp.quicksum(
            transport_cost[i][j] * x[i, j]
            for i in regions
            for j in regions
            if i != j
        ),
        GRB.MINIMIZE,
    )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    if model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    return {"objective": None, "status": "not solved: status %d" % model.Status}