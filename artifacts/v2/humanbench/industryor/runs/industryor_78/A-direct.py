import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    # Item values read from params
    items = {
        "painting": params["painting_value"],
        "bust": params["bust_value"],
        "vase": params["vase_value"],
        "porsche": params["porsche_value"],
        "diamonds": params["diamond_value"] * params["diamond_count"],
        "sofa": params["sofa_value"],
        "dogs": params["dog_value"] * params["dog_count"],
        "sculpture": params["sculpture_value"],
        "sailboat": params["sailboat_value"],
        "harley": params["harley_value"],
        "cavour": params["cavour_furniture_value"],
    }

    model = pyo.ConcreteModel()

    model.ITEMS = pyo.Set(initialize=list(items.keys()))

    # x[i] = 1 if son A gets whole item i, 0 if son B gets it
    model.x = pyo.Var(model.ITEMS, domain=pyo.Binary)

    # Deviation variable d >= |sum_A - sum_B|
    model.d = pyo.Var(domain=pyo.NonNegativeReals)

    total = sum(items.values())
    model.total = pyo.Param(initialize=total, mutable=False)

    # Difference: sum_A - sum_B = 2*sum_A - total
    def diff_rule(mdl):
        sum_a = sum(items[i] * mdl.x[i] for i in items)
        return mdl.d >= 2 * sum_a - total
    model.diff_pos = pyo.Constraint(rule=diff_rule)

    def diff_rule_neg(mdl):
        sum_a = sum(items[i] * mdl.x[i] for i in items)
        return mdl.d >= total - 2 * sum_a
    model.diff_neg = pyo.Constraint(rule=diff_rule_neg)

    model.obj = pyo.Objective(expr=model.d, sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}