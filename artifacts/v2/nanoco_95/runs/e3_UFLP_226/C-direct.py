import gurobipy as gp
from gurobipy import GRB


def solve(params):
    investment_costs = params["location_investment_cost"]
    distance_matrix = params["distance_matrix"]

    num_demand = len(distance_matrix)
    num_sites = len(investment_costs)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # y[j] = 1 if site j is opened
    y = model.addVars(num_sites, vtype=GRB.BINARY, name="y")

    # x[i, j] = 1 if demand point i is assigned to site j
    x = model.addVars(num_demand, num_sites, vtype=GRB.BINARY, name="x")

    # Objective: investment costs + travel distances
    model.setObjective(
        gp.quicksum(investment_costs[j] * y[j] for j in range(num_sites))
        + gp.quicksum(
            distance_matrix[i][j] * x[i, j]
            for i in range(num_demand)
            for j in range(num_sites)
        ),
        GRB.MINIMIZE,
    )

    # Each demand point assigned to exactly one site
    for i in range(num_demand):
        model.addConstr(
            gp.quicksum(x[i, j] for j in range(num_sites)) == 1,
            name=f"assign_{i}",
        )

    # Assignment only to open sites
    for i in range(num_demand):
        for j in range(num_sites):
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