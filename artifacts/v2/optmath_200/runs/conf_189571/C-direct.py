import gurobipy as gp
from gurobipy import GRB
import random

def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost_f0_c0 = params["cost_f0_c0"]
    cost_f0_c1 = params["cost_f0_c1"]
    cost_f1_c0 = params["cost_f1_c0"]
    cost_f2_c1 = params["cost_f2_c1"]
    cost_range_low = params["cost_range_low"]
    cost_range_high = params["cost_range_high"]

    num_facilities = 10
    num_centers = 12

    # Build cost matrix
    # Specific costs for known routes; fill others from cost_range_low/high using a deterministic approach
    # We'll use the midpoint for all unspecified routes, which is a valid interpretation
    # since the problem only specifies 4 specific costs and says others range between low and high.
    # To be deterministic and consistent, use the midpoint for unspecified routes.
    mid_cost = (cost_range_low + cost_range_high) / 2.0

    cost = {}
    for i in range(num_facilities):
        for j in range(num_centers):
            cost[i, j] = mid_cost

    # Override with the specific known costs
    cost[0, 0] = cost_f0_c0
    cost[0, 1] = cost_f0_c1
    cost[1, 0] = cost_f1_c0
    cost[2, 1] = cost_f2_c1

    model = gp.Model("transportation")
    model.setParam("OutputFlag", 0)

    # Decision variables: x[i,j] = units shipped from facility i to center j
    x = {}
    for i in range(num_facilities):
        for j in range(num_centers):
            x[i, j] = model.addVar(lb=0.0, vtype=GRB.CONTINUOUS, name=f"x_{i}_{j}")

    model.update()

    # Objective: minimize total transportation cost
    obj = gp.quicksum(cost[i, j] * x[i, j] for i in range(num_facilities) for j in range(num_centers))
    model.setObjective(obj, GRB.MINIMIZE)

    # Supply constraints
    for i in range(num_facilities):
        model.addConstr(
            gp.quicksum(x[i, j] for j in range(num_centers)) == supply[i],
            name=f"supply_{i}"
        )

    # Demand constraints
    for j in range(num_centers):
        model.addConstr(
            gp.quicksum(x[i, j] for i in range(num_facilities)) == demand[j],
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