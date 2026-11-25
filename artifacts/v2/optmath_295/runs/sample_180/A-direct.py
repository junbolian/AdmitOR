import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    profit_per_unit = params["profit_per_unit"]
    stage_hours = params["stage_hours"]
    time_coeffs = params["time_coeffs"]
    min_production = params["min_production"]
    max_demand = params["max_demand"]

    num_products = len(profit_per_unit)
    num_stages = len(stage_hours)

    model = pyo.ConcreteModel()

    model.Products = pyo.RangeSet(0, num_products - 1)
    model.Stages = pyo.RangeSet(0, num_stages - 1)

    model.x = pyo.Var(model.Products, domain=pyo.NonNegativeReals)

    def profit_rule(m):
        return sum(profit_per_unit[i] * m.x[i] for i in m.Products)

    model.profit = pyo.Objective(rule=profit_rule, sense=pyo.maximize)

    def stage_capacity_rule(m, s):
        return sum(time_coeffs[s][i] * m.x[i] for i in m.Products) <= stage_hours[s]

    model.stage_capacity = pyo.Constraint(model.Stages, rule=stage_capacity_rule)

    def min_prod_rule(m, i):
        return m.x[i] >= min_production[i]

    model.min_prod = pyo.Constraint(model.Products, rule=min_prod_rule)

    def max_demand_rule(m, i):
        return m.x[i] <= max_demand[i]

    model.max_demand_con = pyo.Constraint(model.Products, rule=max_demand_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.profit))
    return {"objective": obj_val, "status": "optimal"}