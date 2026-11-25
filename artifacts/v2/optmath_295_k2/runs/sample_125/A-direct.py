import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    profit = params["profit"]
    time_per_unit = params["time_per_unit"]
    capacity_hours = params["capacity_hours"]
    min_production = params["min_production"]
    max_production = params["max_production"]

    n = len(profit)
    products = list(range(n))

    model = pyo.ConcreteModel()

    model.x = pyo.Var(products, bounds=lambda m, i: (min_production[i], max_production[i]))

    def obj_rule(m):
        return sum(profit[i] * m.x[i] for i in products)

    model.total_profit = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    def capacity_rule(m):
        return sum(time_per_unit[i] * m.x[i] for i in products) <= capacity_hours

    model.capacity = pyo.Constraint(rule=capacity_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_profit))
    return {"objective": obj_val, "status": "optimal"}