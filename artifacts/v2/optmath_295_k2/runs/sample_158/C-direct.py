import gurobipy as gp
from gurobipy import GRB
import numbers

def solve(params):
    demand = params["demand"]
    profit = params["profit"]

    num_companies = 3
    num_markets = 4
    num_products = 2

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # x[c, m, p] = units supplied by company c to market m of product p
    x = model.addVars(num_companies, num_markets, num_products, lb=0.0, name="x")

    # Determine profit structure: 3D profit[c][m][p] or 2D profit[c][m*num_products+p]
    if isinstance(profit[0][0], numbers.Number):
        get_profit = lambda c, m, p: profit[c][m * num_products + p]
    else:
        get_profit = lambda c, m, p: profit[c][m][p]

    # Objective: maximize total profit
    model.setObjective(
        gp.quicksum(
            get_profit(c, m, p) * x[c, m, p]
            for c in range(num_companies)
            for m in range(num_markets)
            for p in range(num_products)
        ),
        GRB.MAXIMIZE
    )

    # Demand satisfaction constraints
    for m in range(num_markets):
        for p in range(num_products):
            model.addConstr(
                gp.quicksum(x[c, m, p] for c in range(num_companies)) == demand[m][p],
                name=f"demand_m{m}_p{p}"
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