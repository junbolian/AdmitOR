import gurobipy as gp
from gurobipy import GRB

def solve(params):
    supply = params["supply"]  # dict or list, indexed by district
    demand = params["demand"]  # dict or list, indexed by district
    cost = params["cost"]      # 2D structure, cost[i][j] for i != j

    districts = range(4)

    model = gp.Model("food_redistribution")
    model.setParam("OutputFlag", 0)

    # Decision variables: x[i][j] = units shipped from district i to district j (i != j)
    x = {}
    for i in districts:
        for j in districts:
            if i != j:
                x[i, j] = model.addVar(lb=0.0, vtype=GRB.CONTINUOUS, name=f"x_{i}_{j}")

    # Objective: minimize total transportation cost
    model.setObjective(
        gp.quicksum(cost[i][j] * x[i, j] for i in districts for j in districts if i != j),
        GRB.MINIMIZE
    )

    # Supply constraints: outflow from district i <= surplus (supply[i] - demand[i] if positive)
    # Flow balance: supply[i] + inflow[i] - outflow[i] >= demand[i]
    for i in districts:
        inflow = gp.quicksum(x[j, i] for j in districts if j != i)
        outflow = gp.quicksum(x[i, j] for j in districts if j != i)
        model.addConstr(supply[i] + inflow - outflow >= demand[i], name=f"balance_{i}")

    # Non-negativity already handled by lb=0

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}