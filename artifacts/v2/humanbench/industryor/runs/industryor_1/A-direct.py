import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    children = ["Harry", "Hermione", "Ron", "Fred", "George", "Ginny"]
    cost = {
        "Harry": params["cost_Harry"],
        "Hermione": params["cost_Hermione"],
        "Ron": params["cost_Ron"],
        "Fred": params["cost_Fred"],
        "George": params["cost_George"],
        "Ginny": params["cost_Ginny"],
    }

    model = pyo.ConcreteModel()

    model.x = pyo.Var(children, within=pyo.Binary)

    # Objective: minimize total cost
    model.obj = pyo.Objective(
        expr=sum(cost[c] * model.x[c] for c in children),
        sense=pyo.minimize,
    )

    # Maximum number of children
    model.max_children = pyo.Constraint(
        expr=sum(model.x[c] for c in children) <= params["max_children"]
    )

    # Minimum number of children
    model.min_children = pyo.Constraint(
        expr=sum(model.x[c] for c in children) >= params["min_children"]
    )

    # Ginny must be taken
    model.ginny_required = pyo.Constraint(expr=model.x["Ginny"] == 1)

    # Harry and Fred cannot both be taken
    model.harry_fred = pyo.Constraint(
        expr=model.x["Harry"] + model.x["Fred"] <= 1
    )

    # Harry and George cannot both be taken
    model.harry_george = pyo.Constraint(
        expr=model.x["Harry"] + model.x["George"] <= 1
    )

    # If George is taken, Fred must be taken
    model.george_implies_fred = pyo.Constraint(
        expr=model.x["George"] <= model.x["Fred"]
    )

    # If George is taken, Hermione must be taken
    model.george_implies_hermione = pyo.Constraint(
        expr=model.x["George"] <= model.x["Hermione"]
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}