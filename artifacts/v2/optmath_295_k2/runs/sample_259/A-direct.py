import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    profit = params["profit"]
    time_per_unit = params["time_per_unit"]
    time_capacity = params["time_capacity"]
    min_prod = params["min_prod"]
    max_prod = params["max_prod"]

    n = len(profit)
    products = list(range(n))

    model = pyo.ConcreteModel()

    model.x = pyo.Var(products, domain=pyo.NonNegativeReals)

    def obj_rule(m):
        return sum(profit[i] * m.x[i] for i in products)

    model.total_profit = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    def time_rule(m):
        return sum(time_per_unit[i] * m.x[i] for i in products) <= time_capacity

    model.time_capacity_con = pyo.Constraint(rule=time_rule)

    def min_rule(m, i):
        return m.x[i] >= min_prod[i]

    model.min_con = pyo.Constraint(products, rule=min_rule)

    def max_rule(m, i):
        return m.x[i] <= max_prod[i]

    model.max_con = pyo.Constraint(products, rule=max_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_profit))
    return {"objective": obj_val, "status": "optimal"}