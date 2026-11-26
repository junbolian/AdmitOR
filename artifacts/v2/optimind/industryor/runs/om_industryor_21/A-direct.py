import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    products = ["shirt", "short_sleeve", "casual_cloth"]

    labor_list = params["labor_per_unit"]
    material_list = params["material_per_unit"]
    price_list = params["selling_price"]
    vcost_list = params["variable_cost"]
    labor_cap = params["labor_capacity"]
    material_cap = params["material_capacity"]
    fixed_list = [
        params["fixed_cost_shirt"],
        params["fixed_cost_short_sleeve"],
        params["fixed_cost_casual_cloth"],
    ]

    labor = dict(zip(products, labor_list))
    material = dict(zip(products, material_list))
    price = dict(zip(products, price_list))
    vcost = dict(zip(products, vcost_list))
    fixed = dict(zip(products, fixed_list))

    model = pyo.ConcreteModel()
    model.P = pyo.Set(initialize=products, ordered=True)

    model.x = pyo.Var(model.P, domain=pyo.NonNegativeReals)
    model.y = pyo.Var(model.P, domain=pyo.Binary)

    bigM = {}
    for p in products:
        if labor[p] > 0 and material[p] > 0:
            bigM[p] = min(labor_cap / labor[p], material_cap / material[p])
        elif labor[p] > 0:
            bigM[p] = labor_cap / labor[p]
        elif material[p] > 0:
            bigM[p] = material_cap / material[p]
        else:
            bigM[p] = 0.0

    def labor_rule(m):
        return sum(labor[p] * m.x[p] for p in m.P) <= labor_cap

    def material_rule(m):
        return sum(material[p] * m.x[p] for p in m.P) <= material_cap

    def link_rule(m, p):
        return m.x[p] <= bigM[p] * m.y[p]

    model.labor_con = pyo.Constraint(rule=labor_rule)
    model.material_con = pyo.Constraint(rule=material_rule)
    model.link_con = pyo.Constraint(model.P, rule=link_rule)

    def obj_rule(m):
        contribution = sum((price[p] - vcost[p]) * m.x[p] for p in m.P)
        fixed_cost = sum(fixed[p] * m.y[p] for p in m.P)
        return contribution - fixed_cost

    model.profit = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.profit))
    return {"objective": obj_val, "status": "optimal"}