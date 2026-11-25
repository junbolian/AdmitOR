import gurobipy as gp
from gurobipy import GRB


def solve(params):
    num_hubs = 5
    num_locations = 19

    fixed_cost = [params[f"fixed_cost_hub_{j}"] for j in range(num_hubs)]
    response_time = params["response_time"]

    model = gp.Model("ems_hub_location")
    model.Params.OutputFlag = 0

    y = model.addVars(num_hubs, vtype=GRB.BINARY, name="y")
    x = model.addVars(num_locations, num_hubs, vtype=GRB.BINARY, name="x")

    model.setObjective(
        gp.quicksum(fixed_cost[j] * y[j] for j in range(num_hubs))
        + gp.quicksum(
            response_time[i][j] * x[i, j]
            for i in range(num_locations)
            for j in range(num_hubs)
        ),
        GRB.MINIMIZE,
    )

    for i in range(num_locations):
        model.addConstr(
            gp.quicksum(x[i, j] for j in range(num_hubs)) == 1,
            name=f"assign_{i}",
        )

    for i in range(num_locations):
        for j in range(num_hubs):
            model.addConstr(x[i, j] <= y[j], name=f"link_{i}_{j}")

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    else:
        return {"objective": None, "status": f"status_{model.status}"}