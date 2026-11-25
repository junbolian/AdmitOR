# IR: {"sets":{"products":"0..5","stages":"0..10"},"params":{"profit":"profit[p]","stage_capacity":"stage_capacity[s]","stage_time":"stage_time[s][p]","min_production":"min_production[p]","demand_limit":"demand_limit[p]"},"variables":{"production[p]":"nonnegative continuous"},"constraints":["For each stage s: sum(stage_time[s,p] * production[p] for p in products) <= stage_capacity[s]","For each product p: production[p] >= min_production[p]","For each product p: production[p] <= demand_limit[p]"],"objective":"maximize sum(profit[p] * production[p] for p in products)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve using product-indexed vectors and a stage-by-product time matrix."""
    model = pyo.ConcreteModel()

    model.products = pyo.RangeSet(0, 5)
    model.stages = pyo.RangeSet(0, 10)

    model.profit = pyo.Param(
        model.products,
        initialize={
            product: params["profit"][product]
            for product in model.products
        },
    )
    model.stage_capacity = pyo.Param(
        model.stages,
        initialize={
            stage: params["stage_capacity"][stage]
            for stage in model.stages
        },
    )
    model.stage_time = pyo.Param(
        model.stages,
        model.products,
        initialize={
            (stage, product): params["stage_time"][stage][product]
            for stage in model.stages
            for product in model.products
        },
    )
    model.min_production = pyo.Param(
        model.products,
        initialize={
            product: params["min_production"][product]
            for product in model.products
        },
    )
    model.demand_limit = pyo.Param(
        model.products,
        initialize={
            product: params["demand_limit"][product]
            for product in model.products
        },
    )

    model.production = pyo.Var(
        model.products,
        domain=pyo.NonNegativeReals,
    )

    def stage_capacity_rule(mod, stage):
        return sum(
            mod.stage_time[stage, product] * mod.production[product]
            for product in mod.products
        ) <= mod.stage_capacity[stage]

    model.stage_capacity_constraints = pyo.Constraint(
        model.stages,
        rule=stage_capacity_rule,
    )

    def minimum_production_rule(mod, product):
        return mod.production[product] >= mod.min_production[product]

    model.minimum_production_constraints = pyo.Constraint(
        model.products,
        rule=minimum_production_rule,
    )

    def demand_limit_rule(mod, product):
        return mod.production[product] <= mod.demand_limit[product]

    model.demand_limit_constraints = pyo.Constraint(
        model.products,
        rule=demand_limit_rule,
    )

    model.total_profit = pyo.Objective(
        expr=sum(
            model.profit[product] * model.production[product]
            for product in model.products
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "infeasible_or_failed"}

    try:
        obj_val = float(pyo.value(model.total_profit))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}