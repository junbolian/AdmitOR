import gurobipy as gp
from gurobipy import GRB

def solve(params):
    supply = {}
    for i in range(4):
        for p in range(2):
            supply[(i, p)] = params[f"supply_origin{i}_product{p}"]

    demand = {}
    for j in range(5):
        for p in range(2):
            demand[(j, p)] = params[f"demand_dest{j}_product{p}"]

    cost = params["cost_matrix"]
    capacity = params["capacity_matrix"]

    origins = range(4)
    dests = range(5)
    products = range(2)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    x = model.addVars(origins, dests, products, lb=0.0, name="x")

    model.setObjective(
        gp.quicksum(cost[i][j][p] * x[i, j, p] for i in origins for j in dests for p in products),
        GRB.MINIMIZE
    )

    for i in origins:
        for p in products:
            model.addConstr(
                gp.quicksum(x[i, j, p] for j in dests) == supply[(i, p)],
                name=f"supply_{i}_{p}"
            )

    for j in dests:
        for p in products:
            model.addConstr(
                gp.quicksum(x[i, j, p] for i in origins) == demand[(j, p)],
                name=f"demand_{j}_{p}"
            )

    for i in origins:
        for j in dests:
            model.addConstr(
                gp.quicksum(x[i, j, p] for p in products) <= capacity[i][j],
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