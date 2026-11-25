import gurobipy as gp
from gurobipy import GRB


def solve(params):
    fixed_cost = params["fixed_cost"]
    variable_cost = params["variable_cost"]
    min_production = params["min_production"]
    max_production = params["max_production"]
    monthly_demand = params["monthly_demand"]

    factories = range(3)
    months = range(4)

    model = gp.Model("multi_factory_scheduling")
    model.Params.OutputFlag = 0

    run = model.addVars(factories, months, vtype=GRB.BINARY, name="run")
    prod = model.addVars(factories, months, lb=0.0, vtype=GRB.CONTINUOUS, name="prod")

    model.setObjective(
        gp.quicksum(
            fixed_cost[f] * run[f, t] + variable_cost[f] * prod[f, t]
            for f in factories
            for t in months
        ),
        GRB.MINIMIZE,
    )

    for f in factories:
        for t in months:
            model.addConstr(prod[f, t] >= min_production[f] * run[f, t], name=f"minp_{f}_{t}")
            model.addConstr(prod[f, t] <= max_production[f] * run[f, t], name=f"maxp_{f}_{t}")

    for t in months:
        model.addConstr(
            gp.quicksum(prod[f, t] for f in factories) >= monthly_demand[t],
            name=f"demand_{t}",
        )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    if model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    if model.Status == GRB.INF_OR_UNBD:
        return {"objective": None, "status": "infeasible_or_unbounded"}
    return {"objective": None, "status": f"status_{model.Status}"}