import gurobipy as gp
from gurobipy import GRB

def solve(params):
    min_production = params["min_production"]
    max_production = params["max_production"]
    monthly_demand = params["monthly_demand"]
    fixed_cost = params["fixed_cost"]
    variable_cost = params["variable_cost"]

    num_factories = len(min_production)
    num_months = len(monthly_demand)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # run[f, t] = 1 if factory f is operational in month t
    run = model.addVars(num_factories, num_months, vtype=GRB.BINARY, name="run")
    # production[f, t] = units produced by factory f in month t
    production = model.addVars(num_factories, num_months, lb=0.0, name="production")

    # Objective: minimize total fixed + variable costs
    model.setObjective(
        gp.quicksum(
            fixed_cost[f] * run[f, t] + variable_cost[f] * production[f, t]
            for f in range(num_factories)
            for t in range(num_months)
        ),
        GRB.MINIMIZE
    )

    for f in range(num_factories):
        for t in range(num_months):
            # production >= min_production * run
            model.addConstr(
                production[f, t] >= min_production[f] * run[f, t],
                name=f"min_prod_f{f}_t{t}"
            )
            # production <= max_production * run
            model.addConstr(
                production[f, t] <= max_production[f] * run[f, t],
                name=f"max_prod_f{f}_t{t}"
            )

    for t in range(num_months):
        model.addConstr(
            gp.quicksum(production[f, t] for f in range(num_factories)) >= monthly_demand[t],
            name=f"demand_t{t}"
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