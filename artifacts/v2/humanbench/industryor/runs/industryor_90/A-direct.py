import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    products = ["shirt", "short_sleeve", "casual"]

    labor_per_unit = {
        "shirt": params["labor_per_unit_shirt"],
        "short_sleeve": params["labor_per_unit_short_sleeve"],
        "casual": params["labor_per_unit_casual"],
    }
    material_per_unit = {
        "shirt": params["material_per_unit_shirt"],
        "short_sleeve": params["material_per_unit_short_sleeve"],
        "casual": params["material_per_unit_casual"],
    }
    price = {
        "shirt": params["price_shirt"],
        "short_sleeve": params["price_short_sleeve"],
        "casual": params["price_casual"],
    }
    variable_cost = {
        "shirt": params["variable_cost_shirt"],
        "short_sleeve": params["variable_cost_short_sleeve"],
        "casual": params["variable_cost_casual"],
    }
    fixed_cost = {
        "shirt": params["fixed_cost_shirt"],
        "short_sleeve": params["fixed_cost_short_sleeve"],
        "casual": params["fixed_cost_casual"],
    }
    labor_capacity = params["labor_capacity"]
    material_capacity = params["material_capacity"]

    model = pyo.ConcreteModel()

    model.PRODUCTS = pyo.Set(initialize=products)

    model.x = pyo.Var(model.PRODUCTS, domain=pyo.NonNegativeReals)
    model.y = pyo.Var(model.PRODUCTS, domain=pyo.Binary)

    # Big-M: upper bound on production of any single product
    big_m = max(labor_capacity, material_capacity)

    def labor_rule(m, p):
        return labor_per_unit[p] * m.x[p] <= labor_capacity

    def material_rule(m, p):
        return material_per_unit[p] * m.x[p] <= material_capacity

    def link_rule(m, p):
        return m.x[p] <= big_m * m.y[p]

    model.labor_cap = pyo.Constraint(model.PRODUCTS, rule=labor_rule)
    model.material_cap = pyo.Constraint(model.PRODUCTS, rule=material_rule)
    model.link = pyo.Constraint(model.PRODUCTS, rule=link_rule)

    model.labor_total = pyo.Constraint(
        expr=sum(labor_per_unit[p] * model.x[p] for p in model.PRODUCTS)
        <= labor_capacity
    )
    model.material_total = pyo.Constraint(
        expr=sum(material_per_unit[p] * model.x[p] for p in model.PRODUCTS)
        <= material_capacity
    )

    def profit_rule(m):
        return sum(
            (price[p] - variable_cost[p]) * m.x[p] - fixed_cost[p] * m.y[p]
            for p in m.PRODUCTS
        )

    model.profit = pyo.Objective(rule=profit_rule, sense=pyo.maximize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.profit))
    return {"objective": obj_val, "status": "optimal"}