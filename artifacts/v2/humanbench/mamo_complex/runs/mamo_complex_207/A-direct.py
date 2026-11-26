import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    raws = [1, 2, 3, 4]
    products = ["regular", "premium"]

    octane_raw = {i: params[f"octane_raw_{i}"] for i in raws}
    avail_raw = {i: params[f"availability_raw_{i}"] for i in raws}
    cost_raw = {i: params[f"cost_raw_{i}"] for i in raws}

    octane_min = {
        "regular": params["octane_min_regular"],
        "premium": params["octane_min_premium"],
    }
    price = {
        "regular": params["price_regular"],
        "premium": params["price_premium"],
    }
    demand_max = {
        "regular": params["demand_max_regular"],
        "premium": params["demand_max_premium"],
    }

    model = pyo.ConcreteModel()

    # x[i, p] = barrels of raw i used in product p
    model.x = pyo.Var(raws, products, domain=pyo.NonNegativeReals)

    # Total production of each product
    def production_rule(mdl, p):
        return sum(mdl.x[i, p] for i in raws)

    model.production = pyo.Expression(products, rule=production_rule)

    # Raw availability constraints
    def avail_rule(mdl, i):
        return sum(mdl.x[i, p] for p in products) <= avail_raw[i]

    model.avail_con = pyo.Constraint(raws, rule=avail_rule)

    # Demand constraints
    def demand_rule(mdl, p):
        return mdl.production[p] <= demand_max[p]

    model.demand_con = pyo.Constraint(products, rule=demand_rule)

    # Octane constraints: sum_i octane_raw_i * x[i,p] >= octane_min_p * sum_i x[i,p]
    def octane_rule(mdl, p):
        return (
            sum(octane_raw[i] * mdl.x[i, p] for i in raws)
            >= octane_min[p] * sum(mdl.x[i, p] for i in raws)
        )

    model.octane_con = pyo.Constraint(products, rule=octane_rule)

    # Objective: maximize revenue - raw material cost
    def profit_rule(mdl):
        revenue = sum(price[p] * mdl.production[p] for p in products)
        raw_cost = sum(cost_raw[i] * mdl.x[i, p] for i in raws for p in products)
        return revenue - raw_cost

    model.profit = pyo.Objective(rule=profit_rule, sense=pyo.maximize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.profit))
    return {"objective": obj_val, "status": "optimal"}