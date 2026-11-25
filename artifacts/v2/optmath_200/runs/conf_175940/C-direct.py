import gurobipy as gp
from gurobipy import GRB

def solve(params):
    fixed_cost = params["fixed_cost"]      # list of length 4
    variable_cost = params["variable_cost"]  # list of length 4
    min_production = params["min_production"]  # list of length 4
    max_production = params["max_production"]  # list of length 4
    demand = params["demand"]              # list of length 6

    num_factories = 4
    num_months = 6
    factories = range(num_factories)
    months = range(num_months)

    model = gp.Model("multi_factory_scheduling")
    model.setParam("OutputFlag", 0)

    # Decision variables
    activate = model.addVars(factories, months, vtype=GRB.BINARY, name="activate")
    produce = model.addVars(factories, months, vtype=GRB.CONTINUOUS, lb=0.0, name="produce")

    # Objective: minimize total fixed + variable costs
    model.setObjective(
        gp.quicksum(fixed_cost[f] * activate[f, t] for f in factories for t in months)
        + gp.quicksum(variable_cost[f] * produce[f, t] for f in factories for t in months),
        GRB.MINIMIZE
    )

    # Constraints
    for f in factories:
        for t in months:
            # Production only if activated; min production if activated
            model.addConstr(produce[f, t] >= min_production[f] * activate[f, t],
                            name=f"min_prod_f{f}_t{t}")
            model.addConstr(produce[f, t] <= max_production[f] * activate[f, t],
                            name=f"max_prod_f{f}_t{t}")

    for t in months:
        # Demand satisfaction
        model.addConstr(
            gp.quicksum(produce[f, t] for f in factories) >= demand[t],
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