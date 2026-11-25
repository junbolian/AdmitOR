import gurobipy as gp
from gurobipy import GRB


def solve(params):
    activation_cost = params["activation_cost"]
    production_cost = params["production_cost"]
    min_production = params["min_production"]
    max_production = params["max_production"]
    demand = params["demand"]

    num_factories = len(activation_cost)
    num_months = len(demand)

    model = gp.Model("production_scheduling")
    model.setParam("OutputFlag", 0)

    y = model.addVars(num_factories, num_months, vtype=GRB.BINARY, name="y")
    x = model.addVars(num_factories, num_months, vtype=GRB.CONTINUOUS, lb=0, name="x")

    model.setObjective(
        gp.quicksum(
            activation_cost[i] * y[i, j]
            for i in range(num_factories)
            for j in range(num_months)
        )
        + gp.quicksum(
            production_cost[i] * x[i, j]
            for i in range(num_factories)
            for j in range(num_months)
        ),
        GRB.MINIMIZE,
    )

    for i in range(num_factories):
        for j in range(num_months):
            model.addConstr(x[i, j] >= min_production[i] * y[i, j])
            model.addConstr(x[i, j] <= max_production[i] * y[i, j])

    for j in range(num_months):
        model.addConstr(
            gp.quicksum(x[i, j] for i in range(num_factories)) >= demand[j]
        )

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": "failed"}