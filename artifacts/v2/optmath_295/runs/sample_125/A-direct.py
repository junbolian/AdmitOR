import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    profit_margin = params["profit_margin"]
    time_per_unit = params["time_per_unit"]
    capacity_hours = params["capacity_hours"]
    min_production = params["min_production"]
    max_production = params["max_production"]

    n = len(profit_margin)
    products = range(n)

    model = pyo.ConcreteModel()

    model.x = pyo.Var(products, domain=pyo.NonNegativeReals)

    def profit_rule(m):
        return sum(profit_margin[i] * m.x[i] for i in products)

    model.profit = pyo.Objective(rule=profit_rule, sense=pyo.maximize)

    def capacity_rule(m):
        return sum(time_per_unit[i] * m.x[i] for i in products) <= capacity_hours

    model.capacity_con = pyo.Constraint(rule=capacity_rule)

    def lower_rule(m, i):
        return m.x[i] >= min_production[i]

    model.lower_con = pyo.Constraint(products, rule=lower_rule)

    def upper_rule(m, i):
        return m.x[i] <= max_production[i]

    model.upper_con = pyo.Constraint(products, rule=upper_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.profit))
    return {"objective": obj_val, "status": "optimal"}