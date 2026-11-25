import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_products = 12

    model = pyo.ConcreteModel()

    model.products = pyo.RangeSet(0, num_products - 1)

    profit = params["profit"]
    time_per_unit = params["time_per_unit"]
    capacity_hours = params["capacity_hours"]
    min_production = params["min_production"]
    max_production = params["max_production"]

    model.x = pyo.Var(model.products, domain=pyo.NonNegativeReals)

    def capacity_rule(m):
        return sum(time_per_unit[i] * m.x[i] for i in m.products) <= capacity_hours

    model.capacity_con = pyo.Constraint(rule=capacity_rule)

    def bounds_rule(m, i):
        return (min_production[i], m.x[i], max_production[i])

    model.bounds_con = pyo.Constraint(model.products, rule=bounds_rule)

    def obj_rule(m):
        return sum(profit[i] * m.x[i] for i in m.products)

    model.total_profit = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_profit))

    return {"objective": obj_val, "status": "optimal"}