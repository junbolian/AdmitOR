# IR: {"sets":{"products":"0..5","stages":"0..10"},"params":{"profit":"profit[product]","stage_hours":"stage_hours[stage]","time_coeff":"time_coeff[6*stage+product], row-major","min_commitment":"min_commitment[product]","demand_limit":"demand_limit[product]"},"variables":{"production[product]":"nonnegative continuous"},"constraints":["For each stage: sum(time_coeff[6*stage+product]*production[product] for product) <= stage_hours[stage]","For each product: production[product] >= min_commitment[product]","For each product: production[product] <= demand_limit[product]"],"objective":"maximize sum(profit[product]*production[product] for product)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.products = pyo.RangeSet(0, 5)
    model.stages = pyo.RangeSet(0, 10)

    model.profit = pyo.Param(
        model.products,
        initialize={product: params["profit"][product] for product in model.products},
    )
    model.stage_hours = pyo.Param(
        model.stages,
        initialize={stage: params["stage_hours"][stage] for stage in model.stages},
    )
    model.time_coeff = pyo.Param(
        model.stages,
        model.products,
        initialize={
            (stage, product): params["time_coeff"][6 * stage + product]
            for stage in model.stages
            for product in model.products
        },
    )
    model.min_commitment = pyo.Param(
        model.products,
        initialize={
            product: params["min_commitment"][product]
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

    model.production = pyo.Var(model.products, domain=pyo.NonNegativeReals)

    def stage_capacity_rule(model, stage):
        return sum(
            model.time_coeff[stage, product] * model.production[product]
            for product in model.products
        ) <= model.stage_hours[stage]

    model.stage_capacity = pyo.Constraint(
        model.stages, rule=stage_capacity_rule
    )

    def minimum_production_rule(model, product):
        return model.production[product] >= model.min_commitment[product]

    model.minimum_production = pyo.Constraint(
        model.products, rule=minimum_production_rule
    )

    def maximum_production_rule(model, product):
        return model.production[product] <= model.demand_limit[product]

    model.maximum_production = pyo.Constraint(
        model.products, rule=maximum_production_rule
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
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_profit))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}