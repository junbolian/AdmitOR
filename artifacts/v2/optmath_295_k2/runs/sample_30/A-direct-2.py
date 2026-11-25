import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    profit = params["profit_per_unit"]
    consumption = params["resource_consumption_per_unit"]
    availability = params["resource_availability"]
    limits = params["production_limit"]

    items = [f"item_{i}" for i in range(45)]

    model = pyo.ConcreteModel()
    model.product_set = pyo.Set(initialize=items)

    model.x = pyo.Var(model.product_set, domain=pyo.NonNegativeReals)

    def build_obj(m):
        return sum(profit[i] * m.x[i] for i in m.product_set)
    model.total_profit = pyo.Objective(rule=build_obj, sense=pyo.maximize)

    def resource_rule(m):
        return sum(consumption[i] * m.x[i] for i in m.product_set) <= availability
    model.resource_constraint = pyo.Constraint(rule=resource_rule)

    def limit_rule(m, i):
        return m.x[i] <= limits[i]
    model.limit_constraint = pyo.Constraint(model.product_set, rule=limit_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_profit))
    return {"objective": obj_val, "status": "optimal"}