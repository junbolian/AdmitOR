import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    octane_rating = params["octane_rating"]
    raw_availability = params["raw_availability"]
    raw_cost = params["raw_cost"]
    min_octane_product = params["min_octane_product"]
    selling_price = params["selling_price"]
    max_demand = params["max_demand"]

    raw_types = [0, 1, 2, 3]
    products = [0, 1]  # 0 = regular, 1 = premium

    model = pyo.ConcreteModel()

    model.R = pyo.Set(initialize=raw_types)
    model.P = pyo.Set(initialize=products)

    # x[p, r]: barrels of raw gasoline r used in product p
    model.x = pyo.Var(model.P, model.R, domain=pyo.NonNegativeReals)

    # y[p]: total barrels produced of product p
    model.y = pyo.Var(model.P, domain=pyo.NonNegativeReals)

    def production_rule(m, p):
        return m.y[p] == sum(m.x[p, r] for r in m.R)
    model.production = pyo.Constraint(model.P, rule=production_rule)

    def availability_rule(m, r):
        return sum(m.x[p, r] for p in m.P) <= raw_availability[r]
    model.availability = pyo.Constraint(model.R, rule=availability_rule)

    def demand_rule(m, p):
        return m.y[p] <= max_demand[p]
    model.demand = pyo.Constraint(model.P, rule=demand_rule)

    def octane_rule(m, p):
        return sum(octane_rating[r] * m.x[p, r] for r in m.R) >= \
            min_octane_product[p] * m.y[p]
    model.octane = pyo.Constraint(model.P, rule=octane_rule)

    def profit_rule(m):
        revenue = sum(selling_price[p] * m.y[p] for p in m.P)
        cost = sum(raw_cost[r] * sum(m.x[p, r] for p in m.P) for r in m.R)
        return revenue - cost
    model.profit = pyo.Objective(rule=profit_rule, sense=pyo.maximize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.profit))
    return {"objective": obj_val, "status": "optimal"}