import gurobipy as gp
from gurobipy import GRB

def solve(params):
    price_meaties = params["price_meaties"]
    price_yummies = params["price_yummies"]
    cereal_per_meaties = params["cereal_per_meaties"]
    meat_per_meaties = params["meat_per_meaties"]
    cereal_per_yummies = params["cereal_per_yummies"]
    meat_per_yummies = params["meat_per_yummies"]
    varcost_meaties = params["varcost_meaties"]
    varcost_yummies = params["varcost_yummies"]
    cereal_price = params["cereal_price"]
    meat_price = params["meat_price"]
    cereal_avail = params["cereal_avail"]
    meat_avail = params["meat_avail"]
    meaties_capacity = params["meaties_capacity"]

    model = gp.Model("HealthyPetFood")
    model.setParam("OutputFlag", 0)

    meaties = model.addVar(lb=0.0, name="meaties")
    yummies = model.addVar(lb=0.0, name="yummies")

    cereal_used = cereal_per_meaties * meaties + cereal_per_yummies * yummies
    meat_used = meat_per_meaties * meaties + meat_per_yummies * yummies

    revenue = price_meaties * meaties + price_yummies * yummies
    ingredient_cost = cereal_price * cereal_used + meat_price * meat_used
    var_cost = varcost_meaties * meaties + varcost_yummies * yummies
    profit = revenue - ingredient_cost - var_cost

    model.setObjective(profit, GRB.MAXIMIZE)

    model.addConstr(cereal_used <= cereal_avail, name="cereal_limit")
    model.addConstr(meat_used <= meat_avail, name="meat_limit")
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