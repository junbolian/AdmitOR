import gurobipy as gp
from gurobipy import GRB

def solve(params):
    establishment_cost = list(params["establishment_cost"])
    coverage_radius = params["coverage_radius"]
    distance_matrix = [list(row) for row in params["distance_matrix"]]

    n_sites = len(establishment_cost)
    n_communities = len(distance_matrix)

    model = gp.Model("supply_depot_network")
    model.Params.OutputFlag = 0

    y = model.addVars(n_sites, vtype=GRB.BINARY, name="y")

    model.setObjective(
        gp.quicksum(establishment_cost[j] * y[j] for j in range(n_sites)),
        GRB.MINIMIZE,
    )

    for i in range(n_communities):
        covering = [j for j in range(n_sites) if distance_matrix[i][j] <= coverage_radius]
        if not covering:
            return {"objective": None, "status": "infeasible"}
        model.addConstr(gp.quicksum(y[j] for j in covering) >= 1, name=f"cover_{i}")

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    if model.status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    if model.status == GRB.INF_OR_UNBD:
        return {"objective": None, "status": "infeasible_or_unbounded"}
    if model.status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    return {"objective": None, "status": "failed"}