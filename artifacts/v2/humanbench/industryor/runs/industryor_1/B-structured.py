# IR: {"sets":{"children":["Harry","Hermione","Ron","Fred","George","Ginny"]},"params":["cost_Harry","cost_Hermione","cost_Ron","cost_Fred","cost_George","cost_Ginny","max_children","min_children"],"variables":{"take[children]":"Binary"},"constraints":["sum(take[c] for c in children) <= max_children","sum(take[c] for c in children) >= min_children","take[Ginny] == 1","take[Harry] + take[Fred] <= 1","take[Harry] + take[George] <= 1","take[George] <= take[Fred]","take[George] <= take[Hermione]"],"objective":{"sense":"minimize","expression":"sum(cost[c] * take[c] for c in children)"}}

import pyomo.environ as pyo
from pyomo.common.errors import ApplicationError
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.children = pyo.Set(
        initialize=["Harry", "Hermione", "Ron", "Fred", "George", "Ginny"],
        ordered=True,
    )

    model.cost = pyo.Param(
        model.children,
        initialize={
            "Harry": params["cost_Harry"],
            "Hermione": params["cost_Hermione"],
            "Ron": params["cost_Ron"],
            "Fred": params["cost_Fred"],
            "George": params["cost_George"],
            "Ginny": params["cost_Ginny"],
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

    model.maximum_children_constraint = pyo.Constraint(
        expr=sum(model.take[child] for child in model.children)
        <= model.max_children
    )
    model.minimum_children_constraint = pyo.Constraint(
        expr=sum(model.take[child] for child in model.children)
        >= model.min_children
    )
    model.ginny_required_constraint = pyo.Constraint(
        expr=model.take["Ginny"] == 1
    )
    model.harry_fred_constraint = pyo.Constraint(
        expr=model.take["Harry"] + model.take["Fred"] <= 1
    )
    model.harry_george_constraint = pyo.Constraint(
        expr=model.take["Harry"] + model.take["George"] <= 1
    )
    model.george_requires_fred_constraint = pyo.Constraint(
        expr=model.take["George"] <= model.take["Fred"]
    )
    model.george_requires_hermione_constraint = pyo.Constraint(
        expr=model.take["George"] <= model.take["Hermione"]
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
    except (RuntimeError, ApplicationError):
        return {"objective": None, "status": "infeasible_or_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}