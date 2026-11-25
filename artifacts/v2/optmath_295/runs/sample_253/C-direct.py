import gurobipy as gp
from gurobipy import GRB


def _to_list(v, n):
    """Coerce v to a flat list of length n."""
    if isinstance(v, (list, tuple)):
        result = list(v)
        if len(result) == n:
            return result
        if len(result) == 1:
            return result * n
        if len(result) > n:
            return result[:n]
        return result + [result[-1]] * (n - len(result))
    return [v] * n


def _cap_at(cap, t):
    """Return capacity for period t, accepting scalar, single-element list, or per-period list."""
    if isinstance(cap, (list, tuple)):
        if len(cap) == 1:
            return cap[0]
        return cap[t]
    return cap


def _scalar(v):
    if isinstance(v, (list, tuple)):
        return v[0]
    return v


def solve(params):
    profit_per_unit = _to_list(params["profit_per_unit"], 2)
    holding_cost = _to_list(params["holding_cost"], 2)
    grinder_hours = _to_list(params["grinder_hours_per_unit"], 2)
    drill_hours = _to_list(params["drill_hours_per_unit"], 2)
    borer_hours = _to_list(params["borer_hours_per_unit"], 2)
    grinder_cap = params["grinder_capacity"]
    drill_cap = params["drill_capacity"]
    borer_cap = params["borer_capacity"]
    inv_limit = _to_list(params["inventory_limit"], 2)
    sales_limit = params["sales_limit"]
    target_inv = _to_list(params["target_inventory"], 2)

    products = [0, 1]
    periods = [0, 1, 2, 3]

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    produce = {
        (p, t): model.addVar(lb=0.0, name=f"produce_{p}_{t}")
        for p in products
        for t in periods
    }
    inventory = {
        (p, t): model.addVar(lb=0.0, ub=inv_limit[p], name=f"inventory_{p}_{t}")
        for p in products
        for t in periods
    }
    sell = {
        (p, t): model.addVar(lb=0.0, ub=_scalar(sales_limit[p][t]), name=f"sell_{p}_{t}")
        for p in products
        for t in periods
    }

    model.setObjective(
        gp.quicksum(profit_per_unit[p] * sell[p, t] for p in products for t in periods)
        - gp.quicksum(holding_cost[p] * inventory[p, t] for p in products for t in periods),
        GRB.MAXIMIZE,
    )

    for p in products:
        for t in periods:
            if t == 0:
                model.addConstr(
                    produce[p, t] == sell[p, t] + inventory[p, t],
                    name=f"balance_{p}_{t}",
                )
            else:
                model.addConstr(
                    inventory[p, t - 1] + produce[p, t] == sell[p, t] + inventory[p, t],
                    name=f"balance_{p}_{t}",
                )

    for t in periods:
        model.addConstr(
            gp.quicksum(grinder_hours[p] * produce[p, t] for p in products) <= _cap_at(grinder_cap, t),
            name=f"grinder_{t}",
        )
        model.addConstr(
            gp.quicksum(drill_hours[p] * produce[p, t] for p in products) <= _cap_at(drill_cap, t),
            name=f"drill_{t}",
        )
        model.addConstr(
            gp.quicksum(borer_hours[p] * produce[p, t] for p in products) <= _cap_at(borer_cap, t),
            name=f"borer_{t}",
        )

    for p in products:
        model.addConstr(
            inventory[p, periods[-1]] == _scalar(target_inv[p]),
            name=f"target_inv_{p}",
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