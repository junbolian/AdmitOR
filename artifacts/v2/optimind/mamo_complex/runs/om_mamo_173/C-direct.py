import gurobipy as gp
from gurobipy import GRB

def solve(params):
    initial_supply = params["initial_supply"]
    required_demand = params["required_demand"]
    transfer_cost = params["transfer_cost"]

    n = 7
    facilities = list(range(n))

    # Build full cost matrix.
    # transfer_cost[i] has n-1 entries: costs from facility i to all others
    # listed in ascending order of destination index (skipping i itself).
    cost = {}
    for i in facilities:
        row = transfer_cost[i]
        destinations = [j for j in facilities if j != i]
        for idx, j in enumerate(destinations):
            cost[i, j] = row[idx]

    model = gp.Model("medical_supply_redistribution")
    model.setParam("OutputFlag", 0)

    # Decision variables: x[i,j] = units transferred from i to j
    x = {}
    for i in facilities:
        for j in facilities:
            if i != j:
                x[i, j] = model.addVar(lb=0.0, name=f"x_{i}_{j}")

    model.update()

    # Objective: minimize total transfer cost
    model.setObjective(
        gp.quicksum(cost[i, j] * x[i, j] for i in facilities for j in facilities if i != j),
        GRB.MINIMIZE
    )

    # Flow balance: each facility must end with at least required_demand[i].
    # Surplus stays at the facility (no need to ship excess away).
    # initial_supply[i] + inflow[i] - outflow[i] >= required_demand[i]
    for i in facilities:
        inflow = gp.quicksum(x[j, i] for j in facilities if j != i)
        outflow = gp.quicksum(x[i, j] for j in facilities if j != i)
        model.addConstr(
            initial_supply[i] + inflow - outflow >= required_demand[i],
            name=f"balance_{i}"
        )

    # Outflow cannot exceed available supply at each facility
    for i in facilities:
        inflow = gp.quicksum(x[j, i] for j in facilities if j != i)
        outflow = gp.quicksum(x[i, j] for j in facilities if j != i)
        model.addConstr(
            outflow <= initial_supply[i] + inflow,
            name=f"capacity_{i}"
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