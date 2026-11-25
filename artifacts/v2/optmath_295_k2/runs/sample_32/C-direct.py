import gurobipy as gp
from gurobipy import GRB

def solve(params):
    supply_origin = params["supply_origin"]
    demand_destination = params["demand_destination"]
    cost_matrix = params["cost_matrix"]
    capacity_matrix = params["capacity_matrix"]

    n_origins = len(supply_origin)
    n_destinations = len(demand_destination)

    model = gp.Model("transportation")
    model.Params.OutputFlag = 0

    x = {}
    for i in range(n_origins):
        for j in range(n_destinations):
            x[i, j] = model.addVar(
                lb=0,
                ub=capacity_matrix[i][j],
                vtype=GRB.CONTINUOUS,
                name=f"x_{i}_{j}"
            )

    model.update()

    for i in range(n_origins):
        model.addConstr(
            gp.quicksum(x[i, j] for j in range(n_destinations)) == supply_origin[i],
            name=f"supply_{i}"
        )

    for j in range(n_destinations):
        model.addConstr(
            gp.quicksum(x[i, j] for i in range(n_origins)) == demand_destination[j],
            name=f"demand_{j}"
        )

    model.setObjective(
        gp.quicksum(
            cost_matrix[i][j] * x[i, j]
            for i in range(n_origins)
            for j in range(n_destinations)
        ),
        GRB.MINIMIZE
    )

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    else:
        return {"objective": None, "status": "infeasible"}