import gurobipy as gp
from gurobipy import GRB

def solve(params):
    transport_cost = params["transport_cost"]  # 5x5 matrix (list of lists), 0-indexed or 1-indexed?
    current_supply = params["current_supply"]  # list of 5 values
    demand = params["demand"]                  # list of 5 values

    n = 5
    regions = range(n)

    model = gp.Model("freight_car_relocation")
    model.setParam("OutputFlag", 0)

    # x[i][j] = number of cars moved from region i to region j (i != j)
    x = {}
    for i in regions:
        for j in regions:
            if i != j:
                x[i, j] = model.addVar(lb=0, vtype=GRB.CONTINUOUS, name=f"x_{i}_{j}")

    # Objective: minimize total transport cost
    model.setObjective(
        gp.quicksum(transport_cost[i][j] * x[i, j] for i in regions for j in regions if i != j),
        GRB.MINIMIZE
    )

    # Supply constraints: cars sent out from region i <= available surplus
    # Net flow: supply[i] + inflow[i] - outflow[i] >= demand[i]
    for i in regions:
        inflow = gp.quicksum(x[j, i] for j in regions if j != i)
        outflow = gp.quicksum(x[i, j] for j in regions if j != i)
        model.addConstr(
            current_supply[i] + inflow - outflow >= demand[i],
            name=f"demand_{i}"
        )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": round(model.ObjVal), "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}