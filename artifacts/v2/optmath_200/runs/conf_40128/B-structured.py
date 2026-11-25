# IR: {"sets":{"products":"0..5","stages":"0..10"},"params":{"profit":"profit[p]","stage_capacity":"stage_capacity[s]","stage_time":"stage_time[s][p]","min_production":"min_production[p]","max_demand":"max_demand[p]"},"variables":{"production[p]":"nonnegative continuous"},"constraints":["sum(stage_time[s,p]*production[p] for p in products) <= stage_capacity[s] for each stage s","production[p] >= min_production[p] for each product p","production[p] <= max_demand[p] for each product p"],"objective":"maximize sum(profit[p]*production[p] for p in products)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.products = pyo.RangeSet(0, 5)
    model.stages = pyo.RangeSet(0, 10)

    model.profit = pyo.Param(
        model.products,
        initialize={p: params["profit"][p] for p in model.products},
    )
    model.stage_capacity = pyo.Param(
        model.stages,
        initialize={s: params["stage_capacity"][s] for s in model.stages},
    )
    model.stage_time = pyo.Param(
        model.stages,
        model.products,
        initialize={
            (s, p): params["stage_time"][s][p]
            for s in model.stages
            for p in model.products
        },
    )
    model.min_production = pyo.Param(
        model.products,
        initialize={p: params["min_production"][p] for p in model.products},
    )
    model.max_demand = pyo.Param(
        model.products,
        initialize={p: params["max_demand"][p] for p in model.products},
    )

    model.production = pyo.Var(model.products, domain=pyo.NonNegativeReals)

    def capacity_rule(mod, s):
        return sum(
            mod.stage_time[s, p] * mod.production[p] for p in mod.products
        ) <= mod.stage_capacity[s]

    model.capacity_limits = pyo.Constraint(model.stages, rule=capacity_rule)

    def minimum_rule(mod, p):
        return mod.production[p] >= mod.min_production[p]

    model.minimum_commitments = pyo.Constraint(
        model.products, rule=minimum_rule
    )

    def demand_rule(mod, p):
        return mod.production[p] <= mod.max_demand[p]

    model.demand_limits = pyo.Constraint(model.products, rule=demand_rule)

    model.total_profit = pyo.Objective(
        expr=sum(
            model.profit[p] * model.production[p] for p in model.products
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_profit))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}