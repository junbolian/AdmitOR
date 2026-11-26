# IR: {"sets":{"feeds":[1,2,3,4,5]},"params":{"protein_requirement":"g","mineral_requirement":"g","vitamin_requirement":"mg","protein_content":"g/g; length-5 sequence ordered by feed","mineral_content":"g/g; length-5 sequence ordered by feed","vitamin_content":"mg/g; length-5 sequence ordered by feed","feed_price":"yuan/kg; length-5 sequence ordered by feed"},"variables":{"feed_grams[feed]":"continuous, nonnegative"},"constraints":["sum(protein_content[feed]*feed_grams[feed]) >= protein_requirement","sum(mineral_content[feed]*feed_grams[feed]) >= mineral_requirement","sum(vitamin_content[feed]*feed_grams[feed]) >= vitamin_requirement"],"objective":"minimize sum(feed_price[feed]*feed_grams[feed]/1000), in yuan"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()
    model.feeds = pyo.RangeSet(1, 5)

    model.protein_requirement = pyo.Param(
        initialize=params["protein_requirement"]
    )
    model.mineral_requirement = pyo.Param(
        initialize=params["mineral_requirement"]
    )
    model.vitamin_requirement = pyo.Param(
        initialize=params["vitamin_requirement"]
    )

    model.protein_content = pyo.Param(
        model.feeds,
        initialize={
            feed: params["protein_content"][feed - 1]
            for feed in model.feeds
        },
    )
    model.mineral_content = pyo.Param(
        model.feeds,
        initialize={
            feed: params["mineral_content"][feed - 1]
            for feed in model.feeds
        },
    )
    model.vitamin_content = pyo.Param(
        model.feeds,
        initialize={
            feed: params["vitamin_content"][feed - 1]
            for feed in model.feeds
        },
    )
    model.feed_price = pyo.Param(
        model.feeds,
        initialize={
            feed: params["feed_price"][feed - 1]
            for feed in model.feeds
        },
    )

    model.feed_grams = pyo.Var(
        model.feeds, domain=pyo.NonNegativeReals
    )

    model.protein_minimum = pyo.Constraint(
        expr=sum(
            model.protein_content[feed] * model.feed_grams[feed]
            for feed in model.feeds
        ) >= model.protein_requirement
    )
    model.mineral_minimum = pyo.Constraint(
        expr=sum(
            model.mineral_content[feed] * model.feed_grams[feed]
            for feed in model.feeds
        ) >= model.mineral_requirement
    )
    model.vitamin_minimum = pyo.Constraint(
        expr=sum(
            model.vitamin_content[feed] * model.feed_grams[feed]
            for feed in model.feeds
        ) >= model.vitamin_requirement
    )

    # Convert feed quantities from grams to kilograms for pricing.
    model.total_cost = pyo.Objective(
        expr=sum(
            model.feed_price[feed] * model.feed_grams[feed] / 1000
            for feed in model.feeds
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "a feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}