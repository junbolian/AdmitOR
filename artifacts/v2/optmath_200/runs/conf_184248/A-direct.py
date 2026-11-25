import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    n_products = 6
    n_stages = 12
    products = list(range(n_products))
    stages = list(range(n_stages))

    profit_per_unit = params["profit_per_unit"]
    stage_hours_available = params["stage_hours_available"]
    stage_time_per_unit = params["stage_time_per_unit"]
    min_production = params["min_production"]
    max_demand = params["max_demand"]

    model = pyo.ConcreteModel()

    model.products = pyo.Set(initialize=products)
    model.stages = pyo.Set(initialize=stages)

    model.x = pyo.Var(model.products, domain=pyo.NonNegativeReals,
                      bounds=lambda m, p: (min_production[p], max_demand[p]))

    def stage_limit_rule(m, s):
        return sum(stage_time_per_unit[s][p] * m.x[p] for p in m.products) <= stage_hours_available[s]

    model.stage_limits = pyo.Constraint(model.stages, rule=stage_limit_rule)

    model.obj = pyo.Objective(
        expr=sum(profit_per_unit[p] * model.x[p] for p in model.products),
        sense=pyo.maximize,
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}