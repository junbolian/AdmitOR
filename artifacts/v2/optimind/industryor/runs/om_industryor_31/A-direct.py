import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    item_data = [
        ("painting", params["painting_value"], 1),
        ("bust", params["bust_value"], 1),
        ("vase", params["vase_value"], 1),
        ("porsche", params["porsche_value"], 1),
        ("diamond", params["diamond_value"], 3),
        ("sofa", params["sofa_value"], 1),
        ("dogs", params["dog_value"], 1),
        ("sculpture", params["sculpture_value"], 1),
        ("boat", params["boat_value"], 1),
        ("motorcycle", params["motorcycle_value"], 1),
        ("cavour", params["cavour_furniture_value"], 1),
    ]

    value = {nm: v for nm, v, _ in item_data}
    multiplicity = {nm: k for nm, _, k in item_data}

    model = pyo.ConcreteModel()
    model.item_set = pyo.Set(initialize=[nm for nm, _, _ in item_data])
    model.val = pyo.Param(model.item_set, initialize=value)
    model.mult = pyo.Param(model.item_set, initialize=multiplicity)

    # Integer count of units of each item type given to son A
    model.x = pyo.Var(model.item_set, domain=pyo.NonNegativeIntegers)

    model.bound = pyo.Constraint(
        model.item_set, rule=lambda m, i: m.x[i] <= m.mult[i]
    )

    model.valueA = pyo.Expression(
        expr=sum(model.val[i] * model.x[i] for i in model.item_set)
    )
    total = sum(value[nm] * multiplicity[nm] for nm, _, _ in item_data)

    model.diff_pos = pyo.Var(domain=pyo.NonNegativeReals)
    model.diff_neg = pyo.Var(domain=pyo.NonNegativeReals)

    model.abs_con = pyo.Constraint(
        expr=2 * model.valueA - total == model.diff_pos - model.diff_neg
    )

    model.obj = pyo.Objective(
        expr=model.diff_pos + model.diff_neg, sense=pyo.minimize
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}