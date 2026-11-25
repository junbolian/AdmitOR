import gurobipy as gp
from gurobipy import GRB


def solve(params):
    fixed_cost = params["fixed_cost"]
    variable_cost = params["variable_cost"]
    min_production = params["min_production"]
    max_production = params["max_production"]
    demand = params["demand"]

    num_factories = 5
    num_months = 6

    model = gp.Model("factory_production")
    model.Params.OutputFlag = 0

    y = {}
    x = {}
    for f in range(num_factories):
        for t in range(num_months):
            y[f, t] = model.addVar(vtype=GRB.BINARY, name=f"y_{f}_{t}")
            x[f, t] = model.addVar(
                vtype=GRB.CONTINUOUS,
                lb=0.0,
                ub=float(max_production[f]),
                name=f"x_{f}_{t}",
            )

    model.update()

    for f in range(num_factories):
        for t in range(num_months):
            model.addConstr(
                x[f, t] >= min_production[f] * y[f, t],
                name=f"minlink_{f}_{t}",
            )
            model.addConstr(
                x[f, t] <= max_production[f] * y[f, t],
                name=f"maxlink_{f}_{t}",
            )

    for t in range(num_months):
        model.addConstr(
            gp.quicksum(x[f, t] for f in range(num_factories)) >= demand[t],
            name=f"demand_{t}",
        )

    model.setObjective(
        gp.quicksum(
            fixed_cost[f] * y[f, t]
            for f in range(num_factories)
            for t in range(num_months)
        )
        + gp.quicksum(
            variable_cost[f] * x[f, t]
            for f in range(num_factories)
            for t in range(num_months)
        ),
        GRB.MINIMIZE,
    )

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    if model.status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    return {"objective": None, "status": "failed"}