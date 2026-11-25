import gurobipy as gp
from gurobipy import GRB

def solve(params):
    construction_cost = params["construction_cost"]
    premium_benefit = params["premium_benefit"]
    R1 = params["critical_response_threshold_R1"]
    R2 = params["premium_response_threshold_R2"]
    travel_time = params["travel_time"]

    n_residents = len(travel_time)
    n_sites = len(construction_cost)

    model = gp.Model("ems_station_deployment")
    model.Params.OutputFlag = 0

    x = model.addVars(n_sites, vtype=GRB.BINARY, name="x")
    y = model.addVars(n_residents, vtype=GRB.BINARY, name="y")

    model.setObjective(
        gp.quicksum(construction_cost[j] * x[j] for j in range(n_sites))
        - gp.quicksum(premium_benefit[i] * y[i] for i in range(n_residents)),
        GRB.MINIMIZE,
    )

    for i in range(n_residents):
        covering_sites = [j for j in range(n_sites) if travel_time[i][j] <= R1]
        if not covering_sites:
            return {"objective": None, "status": "infeasible"}
        model.addConstr(
            gp.quicksum(x[j] for j in covering_sites) >= 1,
            name=f"hard_coverage_{i}",
        )

    for i in range(n_residents):
        premium_sites = [j for j in range(n_sites) if travel_time[i][j] <= R2]
        if premium_sites:
            model.addConstr(
                y[i] <= gp.quicksum(x[j] for j in premium_sites),
                name=f"premium_link_{i}",
            )
        else:
            model.addConstr(y[i] == 0, name=f"no_premium_{i}")

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"status_{model.status}"}