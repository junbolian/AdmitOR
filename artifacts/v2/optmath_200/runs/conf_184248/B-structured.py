# IR: {"sets":{"products":[0,1,2,3,4,5],"stages":[0,1,2,3,4,5,6,7,8,9,10,11]},"params":{"profit_per_unit":"products -> real","stage_hours_available":"stages -> real","stage_time_per_unit":"stages x products -> real","min_production":"products -> real","max_demand":"products -> real"},"variables":{"production":"products -> nonnegative continuous real"},"constraints":["For each stage s: sum(stage_time_per_unit[s,p] * production[p] for p in products) <= stage_hours_available[s]","For each product p: production[p] >= min_production[p]","For each product p: production[p] <= max_demand[p]"],"objective":"Maximize sum(profit_per_unit[p] * production[p] for p in products)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.products = pyo.RangeSet(0, 5)
    model.stages = pyo.RangeSet(0, 11)

    model.profit_per_unit = pyo.Param(
        model.products,
        initialize={
            product: params["profit_per_unit"][product]
            for product in model.products
        },
        within=pyo.Reals,
    )

    model.stage_hours_available = pyo.Param(
        model.stages,
        initialize={
            stage: params["stage_hours_available"][stage]
            for stage in model.stages
        },
        within=pyo.Reals,
    )

    model.stage_time_per_unit = pyo.Param(
        model.stages,
        model.products,
        initialize={
            (stage, product): params["stage_time_per_unit"][stage][product]
            for stage in model.stages
            for product in model.products
        },
        within=pyo.Reals,
    )

    model.min_production = pyo.Param(
        model.products,
        initialize={
            product: params["min_production"][product]
            for product in model.products
        },
        within=pyo.Reals,
    )

    model.max_demand = pyo.Param(
        model.products,
        initialize={
            product: params["max_demand"][product]
            for product in model.products
        },
        within=pyo.Reals,
    )

    model.production = pyo.Var(
        model.products,
        domain=pyo.NonNegativeReals,
    )

    def stage_capacity_rule(current_model, stage):
        return sum(
            current_model.stage_time_per_unit[stage, product]
            * current_model.production[product]
            for product in current_model.products
        ) <= current_model.stage_hours_available[stage]

    model.stage_capacity = pyo.Constraint(
        model.stages,
        rule=stage_capacity_rule,
    )

    def minimum_production_rule(current_model, product):
        return (
            current_model.production[product]
            >= current_model.min_production[product]
        )

    model.minimum_commitment = pyo.Constraint(
        model.products,
        rule=minimum_production_rule,
    )

    def demand_limit_rule(current_model, product):
        return (
            current_model.production[product]
            <= current_model.max_demand[product]
        )

    model.demand_limit = pyo.Constraint(
        model.products,
        rule=demand_limit_rule,
    )

    model.total_profit = pyo.Objective(
        expr=sum(
            model.profit_per_unit[product] * model.production[product]
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