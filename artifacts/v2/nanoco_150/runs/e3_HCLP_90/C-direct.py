import gurobipy as gp
from gurobipy import GRB

def solve(params):
    installation_cost = params["installation_cost"]
    district_x = params["district_x"]
    district_y = params["district_y"]
    site_x = params["site_x"]
    site_y = params["site_y"]
    demand = params["demand"]
    distance = params["distance"]
    grant_revenue = params["grant_revenue"]
    coverage_radius = params["coverage_radius"]
    precision_radius = params["precision_radius"]

    num_districts = 27
    num_sites = 10

    model = gp.Model("air_quality_grid")
    model.Params.OutputFlag = 0

    # x[j] = 1 if station deployed at site j
    x = model.addVars(num_sites, vtype=GRB.BINARY, name="x")
    # y[i] = 1 if district i is precision-monitored
    y = model.addVars(num_districts, vtype=GRB.BINARY, name="y")

    # Coverage constraint: every district within coverage_radius of >= 1 deployed station
    for i in range(num_districts):
        covering_sites = [j for j in range(num_sites) if distance[i][j] <= coverage_radius]
        if not covering_sites:
            return {"objective": None, "status": "infeasible: district {} uncovered".format(i + 1)}
        model.addConstr(gp.quicksum(x[j] for j in covering_sites) >= 1, name="coverage_{}".format(i))

    # Precision constraint: y[i] = 1 only if a deployed station is within precision_radius
    for i in range(num_districts):
        precision_sites = [j for j in range(num_sites) if distance[i][j] <= precision_radius]
        if precision_sites:
            model.addConstr(y[i] <= gp.quicksum(x[j] for j in precision_sites), name="precision_{}".format(i))
        else:
            model.addConstr(y[i] == 0, name="precision_{}".format(i))

    # Objective: minimize installation cost - grant revenue
    model.setObjective(
        gp.quicksum(installation_cost[j] * x[j] for j in range(num_sites))
        - gp.quicksum(grant_revenue[i] * y[i] for i in range(num_districts)),
        GRB.MINIMIZE,
    )

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": "failed: status {}".format(model.status)}