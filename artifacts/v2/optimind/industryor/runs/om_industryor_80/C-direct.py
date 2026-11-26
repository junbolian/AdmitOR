import gurobipy as gp
from gurobipy import GRB

def solve(params):
    space_capacity = params["space_capacity"]
    rent_rate = params["rent_rate"]
    area = params["area"]
    min_shops = params["min_shops"]
    max_shops = params["max_shops"]
    profit_1 = params["profit_1"]
    profit_2 = params["profit_2"]
    profit_3 = params["profit_3"]

    n_types = 5

    # Build profit lookup: profit_per_store[i][k] = profit per store when k stores of type i
    profits_by_count = [profit_1, profit_2, profit_3]  # index 0 = 1 store, 1 = 2 stores, 2 = 3 stores

    profit_lookup = {}
    for i in range(n_types):
        for idx, p_list in enumerate(profits_by_count):
            k = idx + 1
            if p_list is not None and p_list[i] is not None:
                profit_lookup[i, k] = p_list[i]

    model = gp.Model("mall_lease")
    model.setParam("OutputFlag", 0)

    # Binary variables: y[i, k] = 1 if exactly k shops of type i are leased
    y = {}
    for i in range(n_types):
        lo = int(min_shops[i])
        hi = int(max_shops[i])
        for k in range(lo, hi + 1):
            y[i, k] = model.addVar(vtype=GRB.BINARY, name=f"y_{i}_{k}")

    model.update()

    # Exactly one count chosen per type
    for i in range(n_types):
        lo = int(min_shops[i])
        hi = int(max_shops[i])
        model.addConstr(
            gp.quicksum(y[i, k] for k in range(lo, hi + 1)) == 1,
            name=f"one_choice_{i}"
        )

    # Space capacity constraint
    space_expr = gp.LinExpr()
    for i in range(n_types):
        lo = int(min_shops[i])
        hi = int(max_shops[i])
        for k in range(lo, hi + 1):
            space_expr += area[i] * k * y[i, k]
    model.addConstr(space_expr <= space_capacity, name="space")

    # Objective: maximize total rent = rent_rate * sum over types of (k * profit_per_store[i,k])
    obj = gp.LinExpr()
    for i in range(n_types):
        lo = int(min_shops[i])
        hi = int(max_shops[i])
        for k in range(lo, hi + 1):
            if (i, k) in profit_lookup:
                total_profit = k * profit_lookup[i, k]
                obj += rent_rate * total_profit * y[i, k]

    model.setObjective(obj, GRB.MAXIMIZE)
    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}