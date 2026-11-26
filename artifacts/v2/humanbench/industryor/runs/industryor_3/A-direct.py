import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    m = pyo.ConcreteModel()

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

    m.cows = pyo.Var(domain=pyo.NonNegativeIntegers)
    m.sheep = pyo.Var(domain=pyo.NonNegativeIntegers)
    m.chickens = pyo.Var(domain=pyo.NonNegativeIntegers)

    m.profit = pyo.Objective(
        expr=cow_profit * m.cows + sheep_profit * m.sheep + chicken_profit * m.chickens,
        sense=pyo.maximize,
    )

    m.manure_constraint = pyo.Constraint(
        expr=cow_manure * m.cows + sheep_manure * m.sheep + chicken_manure * m.chickens
        <= manure_capacity
    )
    m.chicken_constraint = pyo.Constraint(expr=m.chickens <= chicken_max)
    m.cow_constraint = pyo.Constraint(expr=m.cows >= cow_min)
    m.sheep_constraint = pyo.Constraint(expr=m.sheep >= sheep_min)
    m.total_constraint = pyo.Constraint(
        expr=m.cows + m.sheep + m.chickens <= total_animals_max
    )

    Highs().solve(m)
    obj_val = float(pyo.value(m.profit))
    return {"objective": obj_val, "status": "optimal"}