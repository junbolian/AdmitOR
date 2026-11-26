# IR: {"sets":{"children":["Alice","Bob","Charlie","Diana","Ella"]},"params":["cost_alice","cost_bob","cost_charlie","cost_diana","cost_ella","max_children","min_children"],"variables":{"take[children]":"Binary"},"constraints":["sum(take[c] for c in children) <= max_children","sum(take[c] for c in children) >= min_children","take[Bob] == 1","take[Alice] + take[Diana] <= 1","take[Bob] + take[Charlie] <= 1","take[Charlie] <= take[Diana]","take[Diana] <= take[Ella]"],"objective":"minimize sum(cost[c] * take[c] for c in children)"}

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
    )
    model.max_children = pyo.Param(initialize=params["max_children"])
    model.min_children = pyo.Param(initialize=params["min_children"])

    model.take = pyo.Var(model.children, domain=pyo.Binary)

    model.maximum_children_constraint = pyo.Constraint(
        expr=sum(model.take[child] for child in model.children)
        <= model.max_children
    )
    model.minimum_children_constraint = pyo.Constraint(
        expr=sum(model.take[child] for child in model.children)
        >= model.min_children
    )
    model.bob_required_constraint = pyo.Constraint(
        expr=model.take["Bob"] == 1
    )
    model.alice_diana_constraint = pyo.Constraint(
        expr=model.take["Alice"] + model.take["Diana"] <= 1
    )
    model.bob_charlie_constraint = pyo.Constraint(
        expr=model.take["Bob"] + model.take["Charlie"] <= 1
    )
    model.charlie_requires_diana_constraint = pyo.Constraint(
        expr=model.take["Charlie"] <= model.take["Diana"]
    )
    model.diana_requires_ella_constraint = pyo.Constraint(
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
    except RuntimeError:
        return {"objective": None, "status": "infeasible_or_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}