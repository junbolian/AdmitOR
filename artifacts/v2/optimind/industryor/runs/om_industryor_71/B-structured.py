# IR: {"sets":{"children":["Alice","Bob","Charlie","Diana","Ella"]},"params":{"cost_alice":"real","cost_bob":"real","cost_charlie":"real","cost_diana":"real","cost_ella":"real","max_children":"real","min_children":"real"},"variables":{"take[children]":"binary"},"constraints":["sum(take[c] for c in children) <= max_children","sum(take[c] for c in children) >= min_children","take[Bob] == 1","take[Alice] + take[Diana] <= 1","take[Bob] + take[Charlie] <= 1","take[Charlie] <= take[Diana]","take[Diana] <= take[Ella]"],"objective":{"sense":"minimize","expression":"cost_alice*take[Alice] + cost_bob*take[Bob] + cost_charlie*take[Charlie] + cost_diana*take[Diana] + cost_ella*take[Ella]"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.children = pyo.Set(
        initialize=["Alice", "Bob", "Charlie", "Diana", "Ella"],
        ordered=True,
    )

    model.cost = pyo.Param(
        model.children,
        initialize={
            "Alice": params["cost_alice"],
            "Bob": params["cost_bob"],
            "Charlie": params["cost_charlie"],
            "Diana": params["cost_diana"],
            "Ella": params["cost_ella"],
        },
        within=pyo.Reals,
    )
    model.max_children = pyo.Param(
        initialize=params["max_children"], within=pyo.Reals
    )
    model.min_children = pyo.Param(
        initialize=params["min_children"], within=pyo.Reals
    )

    model.take = pyo.Var(model.children, domain=pyo.Binary)

    model.maximum_children = pyo.Constraint(
        expr=sum(model.take[child] for child in model.children)
        <= model.max_children
    )
    model.minimum_children = pyo.Constraint(
        expr=sum(model.take[child] for child in model.children)
        >= model.min_children
    )
    model.bob_required = pyo.Constraint(expr=model.take["Bob"] == 1)
    model.alice_diana_conflict = pyo.Constraint(
        expr=model.take["Alice"] + model.take["Diana"] <= 1
    )
    model.bob_charlie_conflict = pyo.Constraint(
        expr=model.take["Bob"] + model.take["Charlie"] <= 1
    )
    model.charlie_requires_diana = pyo.Constraint(
        expr=model.take["Charlie"] <= model.take["Diana"]
    )
    model.diana_requires_ella = pyo.Constraint(
        expr=model.take["Diana"] <= model.take["Ella"]
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost[child] * model.take[child]
            for child in model.children
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "A feasible solution was not found" in str(exc):
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}