import gurobipy as gp
from gurobipy import GRB

def solve(params):
    min_production = params["min_production"]
    max_production = params["max_production"]
    demand = params["demand"]
    fixed_cost = params["fixed_cost"]
    variable_cost = params["variable_cost"]

    num_factories = len(min_production)
    num_months = len(demand)

    def get_value(arr, f, t):
        v = arr[f]
        try:
            return v[t]
        except (TypeError, IndexError):
            return v

    model = gp.Model("production_scheduling")
    model.Params.OutputFlag = 0

    y = model.addVars(num_factories, num_months, vtype=GRB.BINARY, name="y")
    x = model.addVars(num_factories, num_months, vtype=GRB.CONTINUOUS, name="x")

    model.setObjective(
        gp.quicksum(
            get_value(fixed_cost, f, t) * y[f, t]
            for f in range(num_factories) for t in range(num_months)
        )
        + gp.quicksum(
            get_value(variable_cost, f, t) * x[f, t]
            for f in range(num_factories) for t in range(num_months)
        ),
        GRB.MINIMIZE,
    )

    for f in range(num_factories):
        for t in range(num_months):
            model.addConstr(x[f, t] <= max_production[f] * y[f, t], name=f"upper_{f}_{t}")
            model.addConstr(x[f, t] >= min_production[f] * y[f, t], name=f"lower_{f}_{t}")

    for t in range(num_months):
        model.addConstr(
            gp.quicksum(x[f, t] for f in range(num_factories)) >= demand[t],
            name=f"demand_{t}",
        )

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": "failed"}