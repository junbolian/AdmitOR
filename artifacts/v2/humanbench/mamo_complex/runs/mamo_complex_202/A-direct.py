import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    # Products: 1 and 2
    products = [1, 2]

    assembly_hours = {
        1: params["assembly_hours_type1"],
        2: params["assembly_hours_type2"],
    }
    testing_hours = {
        1: params["testing_hours_type1"],
        2: params["testing_hours_type2"],
    }
    material_cost = {
        1: params["material_cost_type1"],
        2: params["material_cost_type2"],
    }
    price = {
        1: params["price_type1"],
        2: params["price_type2"],
    }

    model.x = pyo.Var(products, domain=pyo.NonNegativeReals)
    model.overtime = pyo.Var(domain=pyo.NonNegativeReals)

    def obj_rule(m):
        revenue = sum(price[p] * m.x[p] for p in products)
        material = sum(material_cost[p] * m.x[p] for p in products)
        overtime_cost = params["overtime_cost_per_hour"] * m.overtime
        return revenue - material - overtime_cost

    model.profit = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    model.assembly_capacity_con = pyo.Constraint(
        expr=sum(assembly_hours[p] * model.x[p] for p in products)
        <= params["assembly_capacity"] + model.overtime
    )

    model.testing_capacity_con = pyo.Constraint(
        expr=sum(testing_hours[p] * model.x[p] for p in products)
        <= params["testing_capacity"]
    )

    model.overtime_max_con = pyo.Constraint(
        expr=model.overtime <= params["overtime_max"]
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.profit))
    return {"objective": obj_val, "status": "optimal"}