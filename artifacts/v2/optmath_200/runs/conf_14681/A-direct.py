import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_products = 6
    num_stages = 11
    products = list(range(num_products))
    stages = list(range(num_stages))

    profit = list(params["profit"])
    stage_capacity = list(params["stage_capacity"])
    time_coeff = params["time_coeff"]
    min_production = list(params["min_production"])
    market_demand = list(params["market_demand"])

    model = pyo.ConcreteModel()

    model.Products = pyo.Set(initialize=products)
    model.Stages = pyo.Set(initialize=stages)

    model.x = pyo.Var(model.Products, domain=pyo.NonNegativeReals)

    def obj_rule(m):
        return sum(profit[p] * m.x[p] for p in m.Products)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    def cap_rule(m, s):
        return sum(time_coeff[s][p] * m.x[p] for p in m.Products) <= stage_capacity[s]

    model.capacity_rule = pyo.Constraint(model.Stages, rule=cap_rule)

    def min_rule(m, p):
        return m.x[p] >= min_production[p]

    model.min_rule = pyo.Constraint(model.Products, rule=min_rule)

    def max_rule(m, p):
        return m.x[p] <= market_demand[p]

    model.max_rule = pyo.Constraint(model.Products, rule=max_rule)

    Highs().solve(model)

    try:
        obj_val = float(pyo.value(model.obj))
    except Exception:
        return {"objective": None, "status": "infeasible"}

    return {"objective": obj_val, "status": "optimal"}