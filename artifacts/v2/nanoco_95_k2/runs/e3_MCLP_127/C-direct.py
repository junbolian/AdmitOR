import gurobipy as gp
from gurobipy import GRB

def solve(params):
    demands = params["demands"]
    zone_coords = params["zone_coords"]
    site_coords = params["site_coords"]
    distances = params["distances"]
    coverage_radius = params["coverage_radius"]
    num_stations = params["num_stations"]

    num_zones = len(demands)
    num_sites = len(site_coords)

    # Precompute coverage: can_cover[z][s] = True if site s is within radius of zone z
    can_cover = [
        [distances[z][s] <= coverage_radius for s in range(num_sites)]
        for z in range(num_zones)
    ]

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # x[s] = 1 if station is installed at site s
    x = model.addVars(num_sites, vtype=GRB.BINARY, name="x")

    # y[z] = 1 if zone z is covered by at least one selected station
    y = model.addVars(num_zones, vtype=GRB.BINARY, name="y")

    # Exactly num_stations stations
    model.addConstr(gp.quicksum(x[s] for s in range(num_sites)) == num_stations, name="cardinality")

    # Zone z can only be covered if at least one covering station is selected
    for z in range(num_zones):
        covering_sites = [s for s in range(num_sites) if can_cover[z][s]]
        if not covering_sites:
            model.addConstr(y[z] == 0, name=f"no_cover_{z}")
        else:
            model.addConstr(
                y[z] <= gp.quicksum(x[s] for s in covering_sites),
                name=f"cover_link_{z}"
            )

    # Maximize total covered demand
    model.setObjective(
        gp.quicksum(demands[z] * y[z] for z in range(num_zones)),
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