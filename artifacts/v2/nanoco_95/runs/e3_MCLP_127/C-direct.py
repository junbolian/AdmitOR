import gurobipy as gp
from gurobipy import GRB

def solve(params):
    demands = params["demands"]
    coverage_radius = params["coverage_radius"]
    distance_matrix = params["distance_matrix"]
    num_stations = params["num_stations_to_install"]

    num_zones = len(demands)
    num_sites = len(distance_matrix[0])

    # Precompute coverage: can_cover[i][j] = 1 if site j covers zone i
    can_cover = [
        [1 if distance_matrix[i][j] <= coverage_radius else 0
         for j in range(num_sites)]
        for i in range(num_zones)
    ]

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # x[j] = 1 if site j is selected
    x = model.addVars(num_sites, vtype=GRB.BINARY, name="x")
    # y[i] = 1 if zone i is covered
    y = model.addVars(num_zones, vtype=GRB.BINARY, name="y")

    # Exactly num_stations sites selected
    model.addConstr(gp.quicksum(x[j] for j in range(num_sites)) == num_stations)

    # Zone i can only be covered if at least one selected site covers it
    for i in range(num_zones):
        covering_sites = [j for j in range(num_sites) if can_cover[i][j]]
        if not covering_sites:
            model.addConstr(y[i] == 0)
        else:
            # y[i] <= sum of x[j] for covering sites
            model.addConstr(y[i] <= gp.quicksum(x[j] for j in covering_sites))

    # Maximize total covered demand
    model.setObjective(
        gp.quicksum(demands[i] * y[i] for i in range(num_zones)),
        GRB.MAXIMIZE
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