import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cow_price = params["cow_price"]
    sheep_price = params["sheep_price"]
    chicken_price = params["chicken_price"]
    cow_feed_cost = params["cow_feed_cost"]
    sheep_feed_cost = params["sheep_feed_cost"]
    chicken_feed_cost = params["chicken_feed_cost"]
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

    model = pyo.ConcreteModel()

    model.cows = pyo.Var(domain=pyo.NonNegativeReals)
    model.sheep = pyo.Var(domain=pyo.NonNegativeReals)
    model.chickens = pyo.Var(domain=pyo.NonNegativeReals)

    model.obj = pyo.Objective(
        expr=cow_profit * model.cows
        + sheep_profit * model.sheep
        + chicken_profit * model.chickens,
        sense=pyo.maximize,
    )

    model.manure_limit = pyo.Constraint(
        expr=manure_per_cow * model.cows
        + manure_per_sheep * model.sheep
        + manure_per_chicken * model.chickens
        <= manure_capacity
    )
    model.chicken_limit = pyo.Constraint(expr=model.chickens <= max_chickens)
    model.cow_min = pyo.Constraint(expr=model.cows >= min_cows)
    model.sheep_min = pyo.Constraint(expr=model.sheep >= min_sheep)
    model.total_limit = pyo.Constraint(
        expr=model.cows + model.sheep + model.chickens <= max_total_animals
    )

    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.obj))
    except Exception:
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}