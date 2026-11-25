def solve(params):
    import gurobipy as gp
    from gurobipy import GRB

    num_companies = 4
    num_products = 2
    num_markets = 3

    demand = {
        (0, 0): params["demand_p0_m0"],
        (1, 0): params["demand_p1_m0"],
        (0, 1): params["demand_p0_m1"],
        (1, 1): params["demand_p1_m1"],
        (0, 2): params["demand_p0_m2"],
        (1, 2): params["demand_p1_m2"],
    }

    profit = {}
    for c in range(num_companies):
        for p in range(num_products):
            for mk in range(num_markets):
                key = f"profit_c{c}_p{p}_m{mk}"
                profit[(c, p, mk)] = params[key]

    model = gp.Model("market_supply")
    model.setParam("OutputFlag", 0)

    x = model.addVars(num_companies, num_products, num_markets, lb=0.0, name="x")

    model.setObjective(
        gp.quicksum(profit[(c, p, mk)] * x[c, p, mk]
                    for c in range(num_companies)
                    for p in range(num_products)
                    for mk in range(num_markets)),
        GRB.MAXIMIZE
    )

    for p in range(num_products):
        for mk in range(num_markets):
            model.addConstr(
                gp.quicksum(x[c, p, mk] for c in range(num_companies)) == demand[(p, mk)],
                name=f"demand_p{p}_m{mk}"
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