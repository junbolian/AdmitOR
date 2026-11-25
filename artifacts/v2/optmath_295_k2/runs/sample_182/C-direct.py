import gurobipy as gp
from gurobipy import GRB


def solve(params):
    min_production = params["min_production"]
    max_production = params["max_production"]
    monthly_demand = params["monthly_demand"]
    fixed_cost = params["fixed_cost"]
    variable_cost = params["variable_cost"]

    n_factories = 6
    n_months = 4

    def _get(data, i, t):
        """Return data[i][t] if data is 2D, else data[i] if 1D (constant across t)."""
        v = data[i]
        try:
            return float(v[t])
        except (TypeError, IndexError, KeyError):
            return float(v)

    model = gp.Model("factory_scheduling")
    model.Params.OutputFlag = 0

    y = {}
    x = {}
    for i in range(n_factories):
        for t in range(n_months):
            y[i, t] = model.addVar(vtype=GRB.BINARY, name=f"y_{i}_{t}")
            x[i, t] = model.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"x_{i}_{t}")

    model.update()

    # Objective: minimize fixed + variable costs
    model.setObjective(
        gp.quicksum(
            _get(fixed_cost, i, t) * y[i, t]
            + _get(variable_cost, i, t) * x[i, t]
            for i in range(n_factories)
            for t in range(n_months)
        ),
        GRB.MINIMIZE,
    )

    # Production bounds linked to run decision
    for i in range(n_factories):
        for t in range(n_months):
            min_p = _get(min_production, i, t)
            max_p = _get(max_production, i, t)
            model.addConstr(x[i, t] >= min_p * y[i, t], name=f"min_prod_{i}_{t}")
            model.addConstr(x[i, t] <= max_p * y[i, t], name=f"max_prod_{i}_{t}")

    # Demand satisfaction per month
    for t in range(n_months):
        demand = float(monthly_demand[t])
        model.addConstr(
            gp.quicksum(x[i, t] for i in range(n_factories)) >= demand,
            name=f"demand_{t}",
        )

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"failed (gurobi status {model.status})"}