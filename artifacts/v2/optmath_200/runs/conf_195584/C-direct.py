import gurobipy as gp
from gurobipy import GRB

def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]
    ship_limit = params["ship_limit"]

    num_facilities = len(supply)
    num_centers = len(demand)

    model = gp.Model("transportation")
    model.setParam("OutputFlag", 0)

    # Decision variables: x[i][j] = units shipped from facility i to center j
    x = [[model.addVar(lb=0.0, ub=ship_limit[i][j], vtype=GRB.CONTINUOUS, name=f"x_{i}_{j}")
          for j in range(num_centers)]
         for i in range(num_facilities)]

    # Objective: minimize total transportation cost
    model.setObjective(
        gp.quicksum(cost[i][j] * x[i][j]
                    for i in range(num_facilities)
                    for j in range(num_centers)),
        GRB.MINIMIZE
    )

    # Supply constraints: total shipped from facility i <= supply[i]
    for i in range(num_facilities):
        model.addConstr(
            gp.quicksum(x[i][j] for j in range(num_centers)) <= supply[i],
            name=f"supply_{i}"
        )

    # Demand constraints: total received at center j >= demand[j]
    for j in range(num_centers):
        model.addConstr(
            gp.quicksum(x[i][j] for i in range(num_facilities)) >= demand[j],
            name=f"demand_{j}"
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