import gurobipy as gp
from gurobipy import GRB

def solve(params):
    initial_supply = params["initial_supply"]
    demand = params["demand"]
    transport_cost = params["transport_cost"]

    n = len(initial_supply)
    regions = list(range(n))

    model = gp.Model("medical_supply_distribution")
    model.setParam("OutputFlag", 0)

    # x[i, j] = units transported from region i to region j (i != j)
    x = {}
    for i in regions:
        for j in regions:
            if i != j:
                x[i, j] = model.addVar(lb=0.0, name=f"x_{i}_{j}")

    # Objective: minimize total transport cost
    model.setObjective(
        gp.quicksum(transport_cost[i][j] * x[i, j] for i in regions for j in regions if i != j),
        GRB.MINIMIZE
    )

    # Flow conservation: for each region, outflow - inflow >= net_supply (supply - demand)
    # Surplus regions ship out excess; deficit regions receive what they lack.
    # Using >= allows surplus to remain undistributed (total supply > total demand).
    for i in regions:
        outflow = gp.quicksum(x[i, j] for j in regions if j != i)
        inflow = gp.quicksum(x[j, i] for j in regions if j != i)
        net_supply = initial_supply[i] - demand[i]
        # net held after transfers = initial_supply[i] - outflow + inflow >= demand[i]
        # => inflow - outflow >= demand[i] - initial_supply[i]
        # => outflow - inflow <= net_supply
        # But we also need each region to meet demand:
        # initial_supply[i] + inflow - outflow >= demand[i]
        model.addConstr(
            initial_supply[i] + inflow - outflow >= demand[i],
            name=f"demand_{i}"
        )

    # Cannot ship more than what the region holds at start plus what it receives
    # Simple bound: outflow <= initial_supply[i] + inflow
    for i in regions:
        outflow = gp.quicksum(x[i, j] for j in regions if j != i)
        inflow = gp.quicksum(x[j, i] for j in regions if j != i)
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