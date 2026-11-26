import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    children = ["alice", "bob", "charlie", "diana", "ella"]

    cost = {
        "alice": params["cost_alice"],
        "bob": params["cost_bob"],
        "charlie": params["cost_charlie"],
        "diana": params["cost_diana"],
        "ella": params["cost_ella"],
    }

    model = pyo.ConcreteModel()
    model.children = pyo.Set(initialize=children, ordered=True)
    model.x = pyo.Var(model.children, domain=pyo.Binary)

    model.obj = pyo.Objective(
        expr=sum(cost[c] * model.x[c] for c in children),
        sense=pyo.minimize,
    )

    # Maximum and minimum number of children taken
    model.max_children = pyo.Constraint(
        expr=sum(model.x[c] for c in children) <= params["max_children"]
    )
    model.min_children = pyo.Constraint(
        expr=sum(model.x[c] for c in children) >= params["min_children"]
    )

    # Bob is definitely taken
    model.bob_required = pyo.Constraint(expr=model.x["bob"] == 1)

    # Alice and Diana cannot both be taken
    model.alice_diana = pyo.Constraint(
        expr=model.x["alice"] + model.x["diana"] <= 1
    )

    # Bob and Charlie cannot both be taken
    model.bob_charlie = pyo.Constraint(
        expr=model.x["bob"] + model.x["charlie"] <= 1
    )

    # If Charlie, then Diana
    model.charlie_diana = pyo.Constraint(
        expr=model.x["charlie"] <= model.x["diana"]
    )

    # If Diana, then Ella
    model.diana_ella = pyo.Constraint(
        expr=model.x["diana"] <= model.x["ella"]
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}