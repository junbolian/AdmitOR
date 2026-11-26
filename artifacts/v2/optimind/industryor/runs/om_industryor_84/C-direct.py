import gurobipy as gp
from gurobipy import GRB

def solve(params):
    price_meaties = params["price_meaties"]
    price_yummies = params["price_yummies"]
    grains_per_meaties = params["grains_per_meaties"]
    meat_per_meaties = params["meat_per_meaties"]
    grains_per_yummies = params["grains_per_yummies"]
    meat_per_yummies = params["meat_per_yummies"]
    varcost_meaties = params["varcost_meaties"]
    varcost_yummies = params["varcost_yummies"]
    grains_price = params["grains_price"]
    meat_price = params["meat_price"]
    grains_avail = params["grains_avail"]
    meat_avail = params["meat_avail"]
    meaties_capacity = params["meaties_capacity"]

    model = gp.Model("HealthyPetFoods")
    model.setParam("OutputFlag", 0)

    # Decision variables: packs produced per month
    meaties = model.addVar(lb=0.0, name="meaties")
    yummies = model.addVar(lb=0.0, name="yummies")

    # Profit per pack = price - raw material cost - variable cost
    profit_meaties = (price_meaties
                      - grains_per_meaties * grains_price
                      - meat_per_meaties * meat_price
                      - varcost_meaties)
    profit_yummies = (price_yummies
                      - grains_per_yummies * grains_price
                      - meat_per_yummies * meat_price
                      - varcost_yummies)

    model.setObjective(
        profit_meaties * meaties + profit_yummies * yummies,
        GRB.MAXIMIZE
    )

    # Grains constraint
    model.addConstr(
        grains_per_meaties * meaties + grains_per_yummies * yummies <= grains_avail,
        name="grains_limit"
    )

    # Meat constraint
    model.addConstr(
        meat_per_meaties * meaties + meat_per_yummies * yummies <= meat_avail,
        name="meat_limit"
    )

    # Machine capacity for Meaties
    model.addConstr(meaties <= meaties_capacity, name="meaties_capacity")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}