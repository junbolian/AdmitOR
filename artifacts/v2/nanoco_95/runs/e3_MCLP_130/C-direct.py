import gurobipy as gp
from gurobipy import GRB

def solve(params):
    service_range = params["service_range_km"]
    demands = params["demands"]
    distances = params["distances"]

    num_communities = len(demands)
    num_sites = len(distances[0])

    # coverage[i][j] = 1 if community i is within range of site j
    coverage = [
        [1 if distances[i][j] <= service_range else 0
         for j in range(num_sites)]
        for i in range(num_communities)
    ]

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # y[j] = 1 if site j is selected
    y = model.addVars(num_sites, vtype=GRB.BINARY, name="y")
    # z[i] = 1 if community i is covered by at least one selected site
    z = model.addVars(num_communities, vtype=GRB.BINARY, name="z")

    # Exactly 2 sites selected
    model.addConstr(gp.quicksum(y[j] for j in range(num_sites)) == 2, name="select_two")

    # Community i can only be covered if at least one selected site covers it
    for i in range(num_communities):
        covering_sites = [j for j in range(num_sites) if coverage[i][j] == 1]
        if not covering_sites:
            model.addConstr(z[i] == 0, name=f"no_cover_{i}")
        else:
            model.addConstr(
                z[i] <= gp.quicksum(y[j] for j in covering_sites),
                name=f"cover_link_{i}"
            )

    # Maximize total demand of covered communities
    model.setObjective(
        gp.quicksum(demands[i] * z[i] for i in range(num_communities)),
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
        return {"objective": None, "status": f"gurobi_status_{model.Status}"}