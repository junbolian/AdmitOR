import gurobipy as gp
from gurobipy import GRB

def solve(params):
    supply_p0 = params["supply_p0_origins"]
    supply_p1 = params["supply_p1_origins"]
    demand_p0 = params["demand_p0_dests"]
    demand_p1 = params["demand_p1_dests"]
    cost_p0 = params["cost_p0"]
    cost_p1 = params["cost_p1"]
    capacity = params["capacity"]

    origins = range(6)
    dests = range(6)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    x0 = model.addVars(origins, dests, lb=0.0, name="x0")
    x1 = model.addVars(origins, dests, lb=0.0, name="x1")

    model.setObjective(
        gp.quicksum(cost_p0[i][j] * x0[i, j] + cost_p1[i][j] * x1[i, j]
                    for i in origins for j in dests),
        GRB.MINIMIZE
    )

    # Supply constraints
    for i in origins:
        model.addConstr(gp.quicksum(x0[i, j] for j in dests) == supply_p0[i], name=f"sup_p0_{i}")
        model.addConstr(gp.quicksum(x1[i, j] for j in dests) == supply_p1[i], name=f"sup_p1_{i}")

    # Demand constraints
    for j in dests:
        model.addConstr(gp.quicksum(x0[i, j] for i in origins) == demand_p0[j], name=f"dem_p0_{j}")
        model.addConstr(gp.quicksum(x1[i, j] for i in origins) == demand_p1[j], name=f"dem_p1_{j}")

    # Capacity constraints
    for i in origins:
        for j in dests:
            model.addConstr(x0[i, j] + x1[i, j] <= capacity[i][j], name=f"cap_{i}_{j}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}