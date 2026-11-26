import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    children = ["Alice", "Bob", "Charlie", "Diana", "Ella"]

    model = pyo.ConcreteModel()
    model.x = pyo.Var(children, domain=pyo.Binary)

    costs = {
        "Alice": params["cost_alice"],
        "Bob": params["cost_bob"],
        "Charlie": params["cost_charlie"],
        "Diana": params["cost_diana"],
        "Ella": params["cost_ella"],
    }

    model.obj = pyo.Objective(
        expr=sum(costs[c] * model.x[c] for c in children),
        sense=pyo.minimize,
    )

    # Constraints
    model.max_children_con = pyo.Constraint(
        expr=sum(model.x[c] for c in children) <= params["max_children"]
    )
    model.min_children_con = pyo.Constraint(
        expr=sum(model.x[c] for c in children) >= params["min_children"]
    )
    # Bob must be taken
    model.bob_con = pyo.Constraint(expr=model.x["Bob"] == 1)
    # Alice and Diana conflict
    model.alice_diana_con = pyo.Constraint(expr=model.x["Alice"] + model.x["Diana"] <= 1)
    # Bob and Charlie conflict
    model.bob_charlie_con = pyo.Constraint(expr=model.x["Bob"] + model.x["Charlie"] <= 1)
    # Charlie requires Diana
    model.charlie_diana_con = pyo.Constraint(expr=model.x["Charlie"] <= model.x["Diana"])
    # Diana requires Ella
    model.diana_ella_con = pyo.Constraint(expr=model.x["Diana"] <= model.x["Ella"])

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}