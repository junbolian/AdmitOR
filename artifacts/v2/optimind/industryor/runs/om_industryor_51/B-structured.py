# IR: {"sets":{"children":["Harry","Hermione","Ron","Fred","George","Ginny"]},"params":["harry_cost","hermione_cost","ron_cost","fred_cost","george_cost","ginny_cost","max_children","min_children"],"variables":{"take[children]":"Binary"},"constraints":["sum(take[c] for c in children) <= max_children","sum(take[c] for c in children) >= min_children","take[Ginny] == 1","take[Harry] + take[Fred] <= 1","take[Harry] + take[George] <= 1","take[George] <= take[Fred]","take[George] <= take[Hermione]"],"objective":{"sense":"minimize","expression":"harry_cost*take[Harry] + hermione_cost*take[Hermione] + ron_cost*take[Ron] + fred_cost*take[Fred] + george_cost*take[George] + ginny_cost*take[Ginny]"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.children = pyo.Set(
        initialize=["Harry", "Hermione", "Ron", "Fred", "George", "Ginny"],
        ordered=True,
    )

    model.trip_cost = pyo.Param(
        model.children,
        initialize={
            "Harry": params["harry_cost"],
            "Hermione": params["hermione_cost"],
            "Ron": params["ron_cost"],
            "Fred": params["fred_cost"],
            "George": params["george_cost"],
            "Ginny": params["ginny_cost"],
        },
        within=pyo.Reals,
    )
    model.maximum_children = pyo.Param(
        initialize=params["max_children"], within=pyo.Reals
    )
    model.minimum_children = pyo.Param(
        initialize=params["min_children"], within=pyo.Reals
    )

    model.take = pyo.Var(model.children, domain=pyo.Binary)

    model.child_limit = pyo.Constraint(
        expr=sum(model.take[child] for child in model.children)
        <= model.maximum_children
    )
    model.child_minimum = pyo.Constraint(
        expr=sum(model.take[child] for child in model.children)
        >= model.minimum_children
    )
    model.ginny_required = pyo.Constraint(expr=model.take["Ginny"] == 1)
    model.harry_fred_conflict = pyo.Constraint(
        expr=model.take["Harry"] + model.take["Fred"] <= 1
    )
    model.harry_george_conflict = pyo.Constraint(
        expr=model.take["Harry"] + model.take["George"] <= 1
    )
    model.george_requires_fred = pyo.Constraint(
        expr=model.take["George"] <= model.take["Fred"]
    )
    model.george_requires_hermione = pyo.Constraint(
        expr=model.take["George"] <= model.take["Hermione"]
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.trip_cost[child] * model.take[child]
            for child in model.children
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}