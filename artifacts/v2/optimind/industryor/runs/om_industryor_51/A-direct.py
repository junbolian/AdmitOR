import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    children = ["harry", "hermione", "ron", "fred", "george", "ginny"]
    costs = {
        "harry": params["harry_cost"],
        "hermione": params["hermione_cost"],
        "ron": params["ron_cost"],
        "fred": params["fred_cost"],
        "george": params["george_cost"],
        "ginny": params["ginny_cost"],
    }
    max_children = params["max_children"]
    min_children = params["min_children"]

    model = pyo.ConcreteModel()

    model.take = pyo.Var(children, domain=pyo.Binary)

    model.cost = pyo.Objective(
        expr=sum(costs[c] * model.take[c] for c in children),
        sense=pyo.minimize,
    )

    model.max_rule = pyo.Constraint(
        expr=sum(model.take[c] for c in children) <= max_children
    )
    model.min_rule = pyo.Constraint(
        expr=sum(model.take[c] for c in children) >= min_children
    )

    # Ginny must be taken
    model.ginny_rule = pyo.Constraint(expr=model.take["ginny"] == 1)

    # If Harry then not Fred
    model.harry_fred_rule = pyo.Constraint(
        expr=model.take["harry"] + model.take["fred"] <= 1
    )

    # If Harry then not George
    model.harry_george_rule = pyo.Constraint(
        expr=model.take["harry"] + model.take["george"] <= 1
    )

    # If George then Fred
    model.george_fred_rule = pyo.Constraint(
        expr=model.take["george"] <= model.take["fred"]
    )

    # If George then Hermione
    model.george_hermione_rule = pyo.Constraint(
        expr=model.take["george"] <= model.take["hermione"]
    )

    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.cost))
    except Exception:
        return {"objective": None, "status": "infeasible"}

    return {"objective": obj_val, "status": "optimal"}