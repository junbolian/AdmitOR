import gurobipy as gp
from gurobipy import GRB

def solve(params):
    supply_p0 = params["supply_p0"]
    supply_p1 = params["supply_p1"]
    demand_p0 = params["demand_p0"]
    demand_p1 = params["demand_p1"]
    cost_p0 = params["cost_p0"]
    cost_p1 = params["cost_p1"]
    route_capacity = params["route_capacity"]

    num_origins = 4
    num_destinations = 6
    origins = range(num_origins)
    destinations = range(num_destinations)

    model = gp.Model("multi_product_transport")
    model.setParam("OutputFlag", 0)

    x0 = model.addVars(origins, destinations, lb=0.0, name="x0")
    x1 = model.addVars(origins, destinations, lb=0.0, name="x1")

    model.setObjective(
        gp.quicksum(
            cost_p0[i][j] * x0[i, j] + cost_p1[i][j] * x1[i, j]
            for i in origins for j in destinations
        ),
        GRB.MINIMIZE
    )

    for i in origins:
        model.addConstr(
            gp.quicksum(x0[i, j] for j in destinations) <= supply_p0[i],
            name=f"supply_p0_{i}"
        )
        model.addConstr(
            gp.quicksum(x1[i, j] for j in destinations) <= supply_p1[i],
            name=f"supply_p1_{i}"
        )

    for j in destinations:
        model.addConstr(
            gp.quicksum(x0[i, j] for i in origins) >= demand_p0[j],
            name=f"demand_p0_{j}"
        )
        model.addConstr(
            gp.quicksum(x1[i, j] for i in origins) >= demand_p1[j],
            name=f"demand_p1_{j}"
        )

    for i in origins:
        for j in destinations:
            model.addConstr(
                x0[i, j] + x1[i, j] <= route_capacity[i][j],
                name=f"capacity_{i}_{j}"
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