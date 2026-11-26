import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    fruits = ["apples", "pears", "oranges", "lemons"]
    profit = {
        "apples": params["profit_apples"],
        "pears": params["profit_pears"],
        "oranges": params["profit_oranges"],
        "lemons": params["profit_lemons"],
    }

    model = pyo.ConcreteModel()

    model.FRUITS = pyo.Set(initialize=fruits)

    model.acres = pyo.Var(model.FRUITS, domain=pyo.NonNegativeReals)
    # Binary indicator: 1 if fruit type is grown (acres > 0)
    model.grown = pyo.Var(model.FRUITS, domain=pyo.Binary)

    big_M = params["total_land"]

    def obj_rule(m):
        return sum(profit[f] * m.acres[f] for f in m.FRUITS)

    model.profit_expr = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    def land_rule(m):
        return sum(m.acres[f] for f in m.FRUITS) <= params["total_land"]

    model.land_constraint = pyo.Constraint(rule=land_rule)

    def apple_pear_rule(m):
        return m.acres["apples"] >= params["apples_vs_pears_ratio"] * m.acres["pears"]

    model.apple_pear_constraint = pyo.Constraint(rule=apple_pear_rule)

    def apple_lemon_rule(m):
        return m.acres["apples"] >= params["apples_vs_lemons_ratio"] * m.acres["lemons"]

    model.apple_lemon_constraint = pyo.Constraint(rule=apple_lemon_rule)

    def orange_lemon_rule(m):
        return m.acres["oranges"] == params["oranges_vs_lemons_ratio"] * m.acres["lemons"]

    model.orange_lemon_constraint = pyo.Constraint(rule=orange_lemon_rule)

    def link_upper_rule(m, f):
        return m.acres[f] <= big_M * m.grown[f]

    model.link_upper = pyo.Constraint(model.FRUITS, rule=link_upper_rule)

    def max_types_rule(m):
        return sum(m.grown[f] for f in m.FRUITS) <= params["max_fruit_types"]

    model.max_types_constraint = pyo.Constraint(rule=max_types_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.profit_expr))
    return {"objective": obj_val, "status": "optimal"}