import gurobipy as gp
from gurobipy import GRB

def solve(params):
    activation_cost = params["activation_cost"]
    production_cost = params["production_cost"]
    min_production = params["min_production"]
    max_production = params["max_production"]
    demand = params["demand"]

    num_factories = 4
    num_months = 4

    model = gp.Model("multi_factory_production")
    model.setParam("OutputFlag", 0)

    # Decision variables
    activate = model.addVars(num_months, num_factories, vtype=GRB.BINARY, name="activate")
    produce = model.addVars(num_months, num_factories, vtype=GRB.CONTINUOUS, lb=0.0, name="produce")

    # Objective: minimize total activation + production costs
    model.setObjective(
        gp.quicksum(
            activation_cost[f] * activate[t, f] + production_cost[f] * produce[t, f]
            for t in range(num_months)
            for f in range(num_factories)
        ),
        GRB.MINIMIZE
    )

    # Constraints
    for t in range(num_months):
        for f in range(num_factories):
            # Production >= min_production * activate
            model.addConstr(produce[t, f] >= min_production[f] * activate[t, f],
                            name=f"min_prod_{t}_{f}")
            # Production <= max_production * activate
            model.addConstr(produce[t, f] <= max_production[f] * activate[t, f],
                            name=f"max_prod_{t}_{f}")

        # Demand satisfaction
        model.addConstr(
            gp.quicksum(produce[t, f] for f in range(num_factories)) >= demand[t],
            name=f"demand_{t}"
        )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver_status_{model.Status}"}