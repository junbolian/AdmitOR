import gurobipy as gp
from gurobipy import GRB

def solve(params):
    num_companies = 3
    num_products = 2
    num_regions = 5

    # Read demand from params
    demand = {}
    for p in range(num_products):
        for r in range(num_regions):
            demand[(p, r)] = params[f"demand_product{p}_region{r}"]

    # Read profit from params
    profit = {}
    for c in range(num_companies):
        for p in range(num_products):
            for r in range(num_regions):
                profit[(c, p, r)] = params[f"profit_company{c}_product{p}_region{r}"]

    model = gp.Model("supply_distribution")
    model.setParam("OutputFlag", 0)

    # Decision variables: quantity supplied by company c of product p to region r
    x = model.addVars(num_companies, num_products, num_regions, lb=0.0, name="x")

    # Objective: maximize total profit
    model.setObjective(
        gp.quicksum(profit[(c, p, r)] * x[c, p, r]
                    for c in range(num_companies)
                    for p in range(num_products)
                    for r in range(num_regions)),
        GRB.MAXIMIZE
    )

    # Demand constraints: total supply of product p to region r equals demand
    for p in range(num_products):
        for r in range(num_regions):
            model.addConstr(
                gp.quicksum(x[c, p, r] for c in range(num_companies)) == demand[(p, r)],
                name=f"demand_p{p}_r{r}"
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