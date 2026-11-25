import gurobipy as gp
from gurobipy import GRB

def solve(params):
    demands = params["demands"]
    zone_coords = params["zone_coords"]
    site_coords = params["site_coords"]
    distances = params["distances"]
    coverage_radius = params["coverage_radius"]
    num_stations = int(params["num_stations"])

    num_zones = len(demands)
    num_sites = len(site_coords)

    model = gp.Model("ev_charging_network")
    model.setParam("OutputFlag", 0)

    x = model.addVars(num_sites, vtype=GRB.BINARY, name="x")
    y = model.addVars(num_zones, vtype=GRB.BINARY, name="y")

    model.addConstr(x.sum() == num_stations, name="cardinality")

    for i in range(num_zones):
        covering_sites = [j for j in range(num_sites) if distances[i][j] <= coverage_radius]
        if covering_sites:
            model.addConstr(
                y[i] <= gp.quicksum(x[j] for j in covering_sites),
                name=f"cover_{i}",
            )
        else:
            model.addConstr(y[i] == 0, name=f"cover_{i}")

    model.setObjective(gp.quicksum(demands[i] * y[i] for i in range(num_zones)), GRB.MAXIMIZE)
    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    if model.status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    if model.status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    if model.status == GRB.INF_OR_UNBD:
        return {"objective": None, "status": "infeasible_or_unbounded"}
    return {"objective": None, "status": "no_solution"}