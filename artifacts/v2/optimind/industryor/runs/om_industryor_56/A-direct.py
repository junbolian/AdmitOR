import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    profit_apples = params["profit_apples"]
    profit_pears = params["profit_pears"]
    profit_oranges = params["profit_oranges"]
    profit_lemons = params["profit_lemons"]
    total_land = params["total_land"]
    apple_vs_pear_ratio = params["apple_vs_pear_ratio"]
    apple_vs_lemon_ratio = params["apple_vs_lemon_ratio"]
    orange_vs_lemon_ratio = params["orange_vs_lemon_ratio"]
    max_fruit_types = params["max_fruit_types"]

    fruits = ["apples", "pears", "oranges", "lemons"]

    model = pyo.ConcreteModel()

    # Continuous acreage variables (acres >= 0)
    model.x = pyo.Var(fruits, domain=pyo.NonNegativeReals)

    # Binary indicators of whether a fruit type is grown
    model.y = pyo.Var(fruits, domain=pyo.Binary)

    # Big-M: maximum possible acres for any single type
    big_m = total_land

    # Link acreage to binary: x <= M * y
    def link_rule(m, f):
        return m.x[f] <= big_m * m.y[f]
    model.link_con = pyo.Constraint(fruits, rule=link_rule)

    # Total land constraint
    def total_land_rule(m):
        return sum(m.x[f] for f in fruits) <= total_land
    model.total_land_con = pyo.Constraint(rule=total_land_rule)

    # Apple >= ratio * pear
    def apple_pear_rule(m):
        return m.x["apples"] >= apple_vs_pear_ratio * m.x["pears"]
    model.apple_pear_con = pyo.Constraint(rule=apple_pear_rule)

    # Apple >= ratio * lemon
    def apple_lemon_rule(m):
        return m.x["apples"] >= apple_vs_lemon_ratio * m.x["lemons"]
    model.apple_lemon_con = pyo.Constraint(rule=apple_lemon_rule)

    # Orange = ratio * lemon if lemons are grown (activated by y["lemons"])
    def orange_lemon_rule(m):
        return m.x["oranges"] >= orange_vs_lemon_ratio * m.x["lemons"]
    model.orange_lemon_con = pyo.Constraint(rule=orange_lemon_rule)

    def orange_lemon_off_rule(m):
        return m.x["oranges"] <= orange_vs_lemon_ratio * m.x["lemons"] + big_m * (1 - m.y["lemons"])
    model.orange_lemon_off_con = pyo.Constraint(rule=orange_lemon_off_rule)

    # At most max_fruit_types fruit types grown
    def max_types_rule(m):
        return sum(m.y[f] for f in fruits) <= max_fruit_types
    model.max_types_con = pyo.Constraint(rule=max_types_rule)

    # Objective: maximize total profit
    profits = {
        "apples": profit_apples,
        "pears": profit_pears,
        "oranges": profit_oranges,
        "lemons": profit_lemons,
    }

    def obj_rule(m):
        return sum(profits[f] * m.x[f] for f in fruits)
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    # Solve with HiGHS
    solver = Highs()
    solver.solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}