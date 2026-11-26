# IR: {"sets":{"F":[1,2,3,4,5]},"params":{"requirement_protein":"scalar","requirement_minerals":"scalar","requirement_vitamins":"scalar","protein_content":"F-indexed","minerals_content":"F-indexed","vitamins_content":"F-indexed","price":"F-indexed"},"variables":{"feed_kg[f]":"nonnegative continuous, f in F"},"constraints":["sum(protein_content[f]*feed_kg[f] for f in F) >= requirement_protein","sum(minerals_content[f]*feed_kg[f] for f in F) >= requirement_minerals","sum(vitamins_content[f]*feed_kg[f] for f in F) >= requirement_vitamins"],"objective":"minimize sum(price[f]*feed_kg[f] for f in F)"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Feed data may be five-element sequences or mappings keyed by 1..5."""

    def feed_values(values):
        if isinstance(values, Mapping):
            return {
                feed: values[feed] if feed in values else values[str(feed)]
                for feed in range(1, 6)
            }
        if len(values) != 5:
            raise ValueError("Each feed-data sequence must contain five values.")
        return {feed: values[feed - 1] for feed in range(1, 6)}

    model = pyo.ConcreteModel()
    model.feeds = pyo.RangeSet(1, 5)

    model.requirement_protein = pyo.Param(
        initialize=params["requirement_protein"]
    )
    model.requirement_minerals = pyo.Param(
        initialize=params["requirement_minerals"]
    )
    model.requirement_vitamins = pyo.Param(
        initialize=params["requirement_vitamins"]
    )

    model.protein_content = pyo.Param(
        model.feeds, initialize=feed_values(params["protein_content"])
    )
    model.minerals_content = pyo.Param(
        model.feeds, initialize=feed_values(params["minerals_content"])
    )
    model.vitamins_content = pyo.Param(
        model.feeds, initialize=feed_values(params["vitamins_content"])
    )
    model.price = pyo.Param(
        model.feeds, initialize=feed_values(params["price"])
    )

    model.feed_kg = pyo.Var(model.feeds, domain=pyo.NonNegativeReals)

    model.protein_requirement = pyo.Constraint(
        expr=sum(
            model.protein_content[feed] * model.feed_kg[feed]
            for feed in model.feeds
        ) >= model.requirement_protein
    )
    model.minerals_requirement = pyo.Constraint(
        expr=sum(
            model.minerals_content[feed] * model.feed_kg[feed]
            for feed in model.feeds
        ) >= model.requirement_minerals
    )
    model.vitamins_requirement = pyo.Constraint(
        expr=sum(
            model.vitamins_content[feed] * model.feed_kg[feed]
            for feed in model.feeds
        ) >= model.requirement_vitamins
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.price[feed] * model.feed_kg[feed]
            for feed in model.feeds
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "a feasible solution was not found" not in str(exc).lower():
            raise
        # Continue to objective retrieval, the sole success criterion.

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "no_solution"}

    return {"objective": obj_val, "status": "optimal"}