# IR: {"sets":{"animals":["cow","sheep","chicken"]},"params":["cow_price","sheep_price","chicken_price","cow_feed_cost","sheep_feed_cost","chicken_feed_cost","cow_manure","sheep_manure","chicken_manure","manure_capacity","chicken_max","cow_min","sheep_min","total_animals_max"],"variables":{"count[animals]":"nonnegative integer"},"constraints":["sum(manure[a]*count[a] for a in animals) <= manure_capacity","count[chicken] <= chicken_max","count[cow] >= cow_min","count[sheep] >= sheep_min","sum(count[a] for a in animals) <= total_animals_max"],"objective":"maximize sum((price[a]-feed_cost[a])*count[a] for a in animals)"}

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
    )
    model.feed_cost = pyo.Param(
        model.animals,
        initialize={
            "cow": params["cow_feed_cost"],
            "sheep": params["sheep_feed_cost"],
            "chicken": params["chicken_feed_cost"],
        },
    )
    model.manure = pyo.Param(
        model.animals,
        initialize={
            "cow": params["cow_manure"],
            "sheep": params["sheep_manure"],
            "chicken": params["chicken_manure"],
        },
    )
    model.manure_capacity = pyo.Param(initialize=params["manure_capacity"])
    model.chicken_max = pyo.Param(initialize=params["chicken_max"])
    model.cow_min = pyo.Param(initialize=params["cow_min"])
    model.sheep_min = pyo.Param(initialize=params["sheep_min"])
    model.total_animals_max = pyo.Param(initialize=params["total_animals_max"])

    model.count = pyo.Var(model.animals, domain=pyo.NonNegativeIntegers)

    model.manure_limit = pyo.Constraint(
        expr=sum(
            model.manure[animal] * model.count[animal]
            for animal in model.animals
        ) <= model.manure_capacity
    )
    model.chicken_limit = pyo.Constraint(
        expr=model.count["chicken"] <= model.chicken_max
    )
    model.cow_requirement = pyo.Constraint(
        expr=model.count["cow"] >= model.cow_min
    )
    model.sheep_requirement = pyo.Constraint(
        expr=model.count["sheep"] >= model.sheep_min
    )
    model.total_limit = pyo.Constraint(
        expr=sum(model.count[animal] for animal in model.animals)
        <= model.total_animals_max
    )

    model.profit = pyo.Objective(
        expr=sum(
            (model.price[animal] - model.feed_cost[animal])
            * model.count[animal]
            for animal in model.animals
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPsi raises this error when no feasible solution can be loaded.
        # Propagate unrelated runtime errors.
        if "A feasible solution was not found" not in str(exc):
            raise

    try:
        obj_val = float(pyo.value(model.profit))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective unavailable"}

    return {"objective": obj_val, "status": "optimal"}