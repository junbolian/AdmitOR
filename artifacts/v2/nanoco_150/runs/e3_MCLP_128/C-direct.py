import gurobipy as gp
from gurobipy import GRB


def solve(params):
    demands = params["demands"]
    coverage_radius = params["coverage_radius"]
    travel_times = params["travel_times"]

    n_communities = len(demands)
    n_depots = len(travel_times[0])

    model = gp.Model("maximal_covering_location")
    model.Params.OutputFlag = 0

    x = model.addVars(n_depots, vtype=GRB.BINARY, name="x")
    y = model.addVars(n_communities, vtype=GRB.BINARY, name="y")

    model.addConstr(gp.quicksum(x[j] for j in range(n_depots)) == 4, "num_depots")

    for i in range(n_communities):
        covering = [j for j in range(n_depots) if travel_times[i][j] <= coverage_radius]
        if covering:
            model.addConstr(
                y[i] <= gp.quicksum(x[j] for j in covering),
                name=f"serve_{i}",
            )
        else:
            model.addConstr(y[i] == 0, name=f"force_unserved_{i}")

    model.setObjective(
        gp.quicksum(demands[i] * y[i] for i in range(n_communities)),
        GRB.MAXIMIZE,
    )

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    if model.status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    return {"objective": None, "status": f"status_{model.status}"}