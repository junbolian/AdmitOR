import gurobipy as gp
from gurobipy import GRB

def solve(params):
    cow_price = params["cow_price"]
    sheep_price = params["sheep_price"]
    chicken_price = params["chicken_price"]
    cow_feed_cost = params["cow_feed_cost"]
    sheep_feed_cost = params["sheep_feed_cost"]
    chicken_feed_cost = params["chicken_feed_cost"]
    cow_manure = params["cow_manure"]
    sheep_manure = params["sheep_manure"]
    chicken_manure = params["chicken_manure"]
    manure_capacity = params["manure_capacity"]
    chicken_max = params["chicken_max"]
    cow_min = params["cow_min"]
    sheep_min = params["sheep_min"]
    total_animals_max = params["total_animals_max"]

    cow_profit = cow_price - cow_feed_cost
    sheep_profit = sheep_price - sheep_feed_cost
    chicken_profit = chicken_price - chicken_feed_cost

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    cows = model.addVar(lb=0, vtype=GRB.INTEGER, name="cows")
    sheep = model.addVar(lb=0, vtype=GRB.INTEGER, name="sheep")
    chickens = model.addVar(lb=0, vtype=GRB.INTEGER, name="chickens")

    model.setObjective(
        cow_profit * cows + sheep_profit * sheep + chicken_profit * chickens,
        GRB.MAXIMIZE
    )

    model.addConstr(cow_manure * cows + sheep_manure * sheep + chicken_manure * chickens <= manure_capacity, "manure")
    model.addConstr(chickens <= chicken_max, "chicken_max")
    model.addConstr(cows >= cow_min, "cow_min")
    model.addConstr(sheep >= sheep_min, "sheep_min")
    model.addConstr(cows + sheep + chickens <= total_animals_max, "total_animals")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}