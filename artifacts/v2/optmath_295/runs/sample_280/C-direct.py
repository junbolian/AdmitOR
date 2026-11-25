import gurobipy as gp
from gurobipy import GRB


def solve(params):
    activation_cost = params["activation_cost"]
    production_cost = params["production_cost"]
    min_production = params["min_production"]
    max_production = params["max_production"]
    demand = params["demand"]
    num_factories = params["num_factories"]
    num_months = params["num_months"]

    factories = range(num_factories)
    months = range(num_months)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Decision variables
    run = model.addVars(factories, months, vtype=GRB.BINARY, name="run")
    production = model.addVars(factories, months, lb=0.0, name="production")

    # Objective: minimize total activation + production costs
    model.setObjective(
        gp.quicksum(
            activation_cost[f] * run[f, t] + production_cost[f] * production[f, t]
            for f in factories
            for t in months
        ),
        GRB.MINIMIZE,
    )

    # Production bounds tied to activation
    for f in factories:
        for t in months:
            # If run[f,t] = 1, production >= min_production[f]
            model.addConstr(
                production[f, t] >= min_production[f] * run[f, t],
                name=f"min_prod_{f}_{t}",
            )
            # If run[f,t] = 1, production <= max_production[f]
            model.addConstr(
                production[f, t] <= max_production[f] * run[f, t],
                name=f"max_prod_{f}_{t}",
            )

    # Demand satisfaction
    for t in months:
        model.addConstr(
            gp.quicksum(production[f, t] for f in factories) >= demand[t],
            name=f"demand_{t}",
        )

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"gurobi_status_{status}"}