# IR: {"sets":{"animals":["cow","sheep","chicken"]},"params":["cow_price","sheep_price","chicken_price","cow_feed_cost","sheep_feed_cost","chicken_feed_cost","cow_profit","sheep_profit","chicken_profit","manure_per_cow","manure_per_sheep","manure_per_chicken","manure_capacity","max_chickens","min_cows","min_sheep","max_total_animals"],"variables":{"count[animals]":"nonnegative integer"},"constraints":["sum(manure_per_animal[a]*count[a] for a in animals) <= manure_capacity","count[chicken] <= max_chickens","count[cow] >= min_cows","count[sheep] >= min_sheep","sum(count[a] for a in animals) <= max_total_animals"],"objective":"maximize sum(profit[a]*count[a] for a in animals); profit[a] uses the supplied net-profit parameter; price and feed-cost parameters are retained as input data"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.animals = pyo.Set(
        initialize=["cow", "sheep", "chicken"],
        ordered=True,
    )

    model.price = pyo.Param(
        model.animals,
        initialize={
            "cow": params["cow_price"],
            "sheep": params["sheep_price"],
            "chicken": params["chicken_price"],
        },
        within=pyo.Reals,
    )
    model.feed_cost = pyo.Param(
        model.animals,
        initialize={
            "cow": params["cow_feed_cost"],
            "sheep": params["sheep_feed_cost"],
            "chicken": params["chicken_feed_cost"],
        },
        within=pyo.Reals,
    )
    model.profit = pyo.Param(
        model.animals,
        initialize={
            "cow": params["cow_profit"],
            "sheep": params["sheep_profit"],
            "chicken": params["chicken_profit"],
        },
        within=pyo.Reals,
    )
    model.manure_per_animal = pyo.Param(
        model.animals,
        initialize={
            "cow": params["manure_per_cow"],
            "sheep": params["manure_per_sheep"],
            "chicken": params["manure_per_chicken"],
        },
        within=pyo.Reals,
    )

    model.manure_capacity = pyo.Param(
        initialize=params["manure_capacity"],
        within=pyo.Reals,
    )
    model.max_chickens = pyo.Param(
        initialize=params["max_chickens"],
        within=pyo.Reals,
    )
    model.min_cows = pyo.Param(
        initialize=params["min_cows"],
        within=pyo.Reals,
    )
    model.min_sheep = pyo.Param(
        initialize=params["min_sheep"],
        within=pyo.Reals,
    )
    model.max_total_animals = pyo.Param(
        initialize=params["max_total_animals"],
        within=pyo.Reals,
    )

    model.count = pyo.Var(model.animals, domain=pyo.NonNegativeIntegers)

    model.manure_limit = pyo.Constraint(
        expr=sum(
            model.manure_per_animal[animal] * model.count[animal]
            for animal in model.animals
        )
        <= model.manure_capacity
    )
    model.chicken_limit = pyo.Constraint(
        expr=model.count["chicken"] <= model.max_chickens
    )
    model.cow_minimum = pyo.Constraint(
        expr=model.count["cow"] >= model.min_cows
    )
    model.sheep_minimum = pyo.Constraint(
        expr=model.count["sheep"] >= model.min_sheep
    )
    model.total_animal_limit = pyo.Constraint(
        expr=sum(model.count[animal] for animal in model.animals)
        <= model.max_total_animals
    )

    model.total_profit = pyo.Objective(
        expr=sum(
            model.profit[animal] * model.count[animal]
            for animal in model.animals
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "a feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_profit))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}