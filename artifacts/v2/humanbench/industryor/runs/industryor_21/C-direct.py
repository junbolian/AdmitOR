import gurobipy as gp
from gurobipy import GRB

def solve(params):
    capacity = params["capacity"]      # list of 6 values, indexed 0..5
    demand = params["demand"]          # list of 6 values
    variable_cost = params["variable_cost"]  # list of 6 values
    fixed_cost = params["fixed_cost"]  # scalar

    n = 6  # number of container types
    types = list(range(n))

    model = gp.Model("RedStarPlastic")
    model.setParam("OutputFlag", 0)

    # x[i][j]: units of container type j used to satisfy demand of type i
    # Only j >= i is allowed (larger or equal capacity substitution)
    x = {}
    for i in types:
        for j in types:
            if j >= i:
                x[i, j] = model.addVar(lb=0, vtype=GRB.INTEGER, name=f"x_{i}_{j}")

    # y[j]: binary, 1 if container type j is produced at all
    y = [model.addVar(vtype=GRB.BINARY, name=f"y_{j}") for j in types]

    # Demand satisfaction: sum of units assigned to meet demand i (using type j >= i) >= demand[i]
    for i in types:
        model.addConstr(
            gp.quicksum(x[i, j] for j in types if j >= i) >= demand[i],
            name=f"demand_{i}"
        )

    # Link x to y: if x[i,j] > 0 then y[j] must be 1
    # Use big-M: x[i,j] <= M * y[j]
    # A safe big-M is sum of all demands (worst case all demand satisfied by one type)
    total_demand = sum(demand)
    for i in types:
        for j in types:
            if j >= i:
                model.addConstr(
                    x[i, j] <= total_demand * y[j],
                    name=f"link_{i}_{j}"
                )

    # Objective: fixed costs + variable costs
    # Variable cost for x[i,j] is variable_cost[j] per unit (the type actually produced)
    obj = gp.quicksum(fixed_cost * y[j] for j in types) + \
          gp.quicksum(variable_cost[j] * x[i, j]
                      for i in types for j in types if j >= i)

    model.setObjective(obj, GRB.MINIMIZE)

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}