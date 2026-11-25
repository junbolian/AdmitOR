import gurobipy as gp
from gurobipy import GRB

def solve(params):
    investment_cost = params["investment_cost"]
    distance_matrix = params["distance_matrix"]

    num_demand = len(distance_matrix)      # 19
    num_sites = len(investment_cost)       # 5

    demand_points = range(num_demand)
    sites = range(num_sites)

    model = gp.Model("ev_charging_network")
    model.setParam("OutputFlag", 0)

    # y[j] = 1 if site j is opened
    y = model.addVars(sites, vtype=GRB.BINARY, name="y")

    # x[i,j] = 1 if demand point i is assigned to site j
    x = model.addVars(demand_points, sites, vtype=GRB.BINARY, name="x")

    # Objective: investment costs + total travel distance
    model.setObjective(
        gp.quicksum(investment_cost[j] * y[j] for j in sites)
        + gp.quicksum(distance_matrix[i][j] * x[i, j] for i in demand_points for j in sites),
        GRB.MINIMIZE
    )

    # Each demand point assigned to exactly one site
    for i in demand_points:
        model.addConstr(gp.quicksum(x[i, j] for j in sites) == 1, name=f"assign_{i}")

    # Assignment only to open sites
    for i in demand_points:
        for j in sites:
            model.addConstr(x[i, j] <= y[j], name=f"link_{i}_{j}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}