import gurobipy as gp
from gurobipy import GRB

def solve(params):
    fixed_cost = params["fixed_cost"]      # list of length 4
    variable_cost = params["variable_cost"]  # list of length 4
    min_production = params["min_production"]  # list of length 4
    max_production = params["max_production"]  # list of length 4
    demand = params["demand"]              # list of length 5

    num_factories = 4
    num_months = 5
    factories = range(num_factories)
    months = range(num_months)

    model = gp.Model("multi_factory_production")
    model.setParam("OutputFlag", 0)

    # Decision variables
    run = model.addVars(factories, months, vtype=GRB.BINARY, name="run")
    produce = model.addVars(factories, months, lb=0.0, name="produce")

    # Objective: minimize total fixed + variable costs
    model.setObjective(
        gp.quicksum(fixed_cost[f] * run[f, t] + variable_cost[f] * produce[f, t]
                    for f in factories for t in months),
        GRB.MINIMIZE
    )

    # Production bounds linked to run decision
    for f in factories:
        for t in months:
            # produce >= min_production[f] * run[f,t]
            model.addConstr(produce[f, t] >= min_production[f] * run[f, t],
                            name=f"min_prod_{f}_{t}")
            # produce <= max_production[f] * run[f,t]
            model.addConstr(produce[f, t] <= max_production[f] * run[f, t],
                            name=f"max_prod_{f}_{t}")

    # Demand satisfaction per month
    for t in months:
        model.addConstr(
            gp.quicksum(produce[f, t] for f in factories) >= demand[t],
            name=f"demand_{t}"
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
        return {"objective": None, "status": f"solver_status_{status}"}