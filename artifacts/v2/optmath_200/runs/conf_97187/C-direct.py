import gurobipy as gp
from gurobipy import GRB

def solve(params):
    demand_p0 = params["demand_p0"]  # list of 4 values
    demand_p1 = params["demand_p1"]  # list of 4 values
    profit_c0_p0 = params["profit_company0_product0"]
    profit_c0_p1 = params["profit_company0_product1"]
    profit_c1_p0 = params["profit_company1_product0"]
    profit_c1_p1 = params["profit_company1_product1"]
    profit_c2_p0 = params["profit_company2_product0"]
    profit_c2_p1 = params["profit_company2_product1"]

    num_companies = 3
    num_products = 2
    num_markets = 4

    # Profit indexed by [company][product][market]
    profit = [
        [profit_c0_p0, profit_c0_p1],
        [profit_c1_p0, profit_c1_p1],
        [profit_c2_p0, profit_c2_p1],
    ]

    demand = [demand_p0, demand_p1]  # demand[product][market]

    model = gp.Model("market_allocation")
    model.setParam("OutputFlag", 0)

    # Decision variables: x[c][p][j] = units supplied by company c of product p to market j
    x = [
        [
            [model.addVar(lb=0.0, name=f"x_c{c}_p{p}_m{j}") for j in range(num_markets)]
            for p in range(num_products)
        ]
        for c in range(num_companies)
    ]

    # Objective: maximize total profit
    obj = gp.quicksum(
        profit[c][p][j] * x[c][p][j]
        for c in range(num_companies)
        for p in range(num_products)
        for j in range(num_markets)
    )
    model.setObjective(obj, GRB.MAXIMIZE)

    # Demand satisfaction constraints: sum over companies == demand for each product and market
    for p in range(num_products):
        for j in range(num_markets):
            model.addConstr(
                gp.quicksum(x[c][p][j] for c in range(num_companies)) == demand[p][j],
                name=f"demand_p{p}_m{j}"
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