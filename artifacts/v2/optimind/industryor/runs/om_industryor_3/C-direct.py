import gurobipy as gp
from gurobipy import GRB

def solve(params):
    cow_profit = params["cow_profit"]
    sheep_profit = params["sheep_profit"]
    chicken_profit = params["chicken_profit"]
    manure_per_cow = params["manure_per_cow"]
    manure_per_sheep = params["manure_per_sheep"]
    manure_per_chicken = params["manure_per_chicken"]
    manure_capacity = params["manure_capacity"]
    max_chickens = params["max_chickens"]
    min_cows = params["min_cows"]
    min_sheep = params["min_sheep"]
    max_total_animals = params["max_total_animals"]

    model = gp.Model("farm")
    model.setParam("OutputFlag", 0)

    cows = model.addVar(vtype=GRB.INTEGER, lb=0, name="cows")
    sheep = model.addVar(vtype=GRB.INTEGER, lb=0, name="sheep")
    chickens = model.addVar(vtype=GRB.INTEGER, lb=0, name="chickens")

    model.setObjective(
        cow_profit * cows + sheep_profit * sheep + chicken_profit * chickens,
        GRB.MAXIMIZE
    )

    model.addConstr(manure_per_cow * cows + manure_per_sheep * sheep + manure_per_chicken * chickens <= manure_capacity, "manure")
    model.addConstr(chickens <= max_chickens, "max_chickens")
    model.addConstr(cows >= min_cows, "min_cows")
    model.addConstr(sheep >= min_sheep, "min_sheep")
    model.addConstr(cows + sheep + chickens <= max_total_animals, "max_total")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}