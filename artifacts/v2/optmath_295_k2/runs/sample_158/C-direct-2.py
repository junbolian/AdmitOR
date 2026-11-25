import gurobipy as gp
from gurobipy import GRB


def solve(params):
    demand = params["demand"]   # demand[m][p] or demand[m*n_products + p]
    profit = params["profit"]   # profit[c][m][p] or flattened variants

    # Structural constants
    n_companies = 3
    n_markets = 4
    n_products = 2

    # Normalize demand to demand_grid[m][p]
    # Handles: list of lists, flat list (market-major, product-minor)
    if hasattr(demand[0], '__len__'):
        demand_grid = [[demand[m][p] for p in range(n_products)] for m in range(n_markets)]
    else:
        demand_grid = [[demand[m * n_products + p] for p in range(n_products)] for m in range(n_markets)]

    # Normalize profit to profit_grid[c][m][p]
    # Handles: list of list of lists, list of flat list (market-major, product-minor), fully flat
    if hasattr(profit[0], '__len__') and hasattr(profit[0][0], '__len__'):
        profit_grid = [[[profit[c][m][p] for p in range(n_products)]
                        for m in range(n_markets)]
                       for c in range(n_companies)]
    elif hasattr(profit[0], '__len__'):
        profit_grid = [[[profit[c][m * n_products + p] for p in range(n_products)]
                        for m in range(n_markets)]
                       for c in range(n_companies)]
    else:
        profit_grid = [[[profit[c * n_markets * n_products + m * n_products + p]
                         for p in range(n_products)]
                        for m in range(n_markets)]
                       for c in range(n_companies)]

    model = gp.Model("distribution")
    model.Params.OutputFlag = 0

    x = {}
    for c in range(n_companies):
        for m in range(n_markets):
            for p in range(n_products):
                x[c, m, p] = model.addVar(lb=0.0, vtype=GRB.CONTINUOUS, name=f"x_{c}_{m}_{p}")

    model.update()

    for m in range(n_markets):
        for p in range(n_products):
            model.addConstr(
                gp.quicksum(x[c, m, p] for c in range(n_companies)) == demand_grid[m][p],
                name=f"demand_{m}_{p}",
            )

    model.setObjective(
        gp.quicksum(
            profit_grid[c][m][p] * x[c, m, p]
            for c in range(n_companies)
            for m in range(n_markets)
            for p in range(n_products)
        ),
        GRB.MAXIMIZE,
    )

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"status_{model.status}"}