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

    model = gp.Model("multi_factory_scheduling")

    # Run decision: 1 if factory f is activated in month t
    run = model.addVars(factories, months, vtype=GRB.BINARY, name="run")
    # Production level of factory f in month t
    prod = model.addVars(factories, months, vtype=GRB.CONTINUOUS, lb=0.0, name="prod")

    # Objective: minimize activation + production costs
    model.setObjective(
        gp.quicksum(
            activation_cost[f] * run[f, t] + production_cost[f] * prod[f, t]
            for f in factories
            for t in months
        ),
        GRB.MINIMIZE,
    )

    # Demand satisfaction per month
    for t in months:
        model.addConstr(
            gp.quicksum(prod[f, t] for f in factories) >= demand[t],
            name=f"demand_{t}",
        )

    # Min/max production linkage with activation
    for f in factories:
        for t in months:
            model.addConstr(
                prod[f, t] >= min_production[f] * run[f, t],
                name=f"minprod_{f}_{t}",
            )
            model.addConstr(
                prod[f, t] <= max_production[f] * run[f, t],
                name=f"maxprod_{f}_{t}",
            )

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    return {"objective": None, "status": f"gurobi_status_{model.status}"}