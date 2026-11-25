import gurobipy as gp
from gurobipy import GRB


def solve(params):
    establishment_cost = params["establishment_cost"]
    coverage_radius = params["coverage_radius"]
    distance_matrix = params["distance_matrix"]

    num_communities = len(distance_matrix)
    num_depots = len(establishment_cost)

    # Build coverage sets: for each community i, which depots j can cover it
    can_cover = {
        i: [j for j in range(num_depots) if distance_matrix[i][j] <= coverage_radius]
        for i in range(num_communities)
    }

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Binary variable: open depot j or not
    open_depot = model.addVars(num_depots, vtype=GRB.BINARY, name="open")

    # Minimize total establishment cost
    model.setObjective(
        gp.quicksum(establishment_cost[j] * open_depot[j] for j in range(num_depots)),
        GRB.MINIMIZE,
    )

    # Every community must be covered by at least one open depot
    for i in range(num_communities):
        if len(can_cover[i]) == 0:
            return {"objective": None, "status": "infeasible: community unreachable"}
        model.addConstr(
            gp.quicksum(open_depot[j] for j in can_cover[i]) >= 1,
            name=f"cover_{i}",
        )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver status {model.Status}"}