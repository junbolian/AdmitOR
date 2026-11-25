# IR: {"sets":{"products":"0..5","stages":"0..10"},"params":{"profit_per_unit":"real[products]","stage_hours":"real[stages]","time_coeffs":"real[stages,products]","min_production":"real[products]","max_demand":"real[products]"},"variables":{"production":"nonnegative continuous[products]"},"constraints":["sum(time_coeffs[s,p]*production[p] for p in products) <= stage_hours[s] for s in stages","production[p] >= min_production[p] for p in products","production[p] <= max_demand[p] for p in products"],"objective":"maximize sum(profit_per_unit[p]*production[p] for p in products)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.products = pyo.RangeSet(0, 5)
    model.stages = pyo.RangeSet(0, 10)

    model.profit_per_unit = pyo.Param(
        model.products,
        initialize={
            product: params["profit_per_unit"][product]
            for product in model.products
        },
        within=pyo.Reals,
    )
    model.stage_hours = pyo.Param(
        model.stages,
        initialize={
            stage: params["stage_hours"][stage]
            for stage in model.stages
        },
        within=pyo.Reals,
    )
    model.time_coeffs = pyo.Param(
        model.stages,
        model.products,
        initialize={
            (stage, product): params["time_coeffs"][stage][product]
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

    def stage_capacity_rule(instance, stage):
        return sum(
            instance.time_coeffs[stage, product]
            * instance.production[product]
            for product in instance.products
        ) <= instance.stage_hours[stage]

    model.stage_capacity = pyo.Constraint(
        model.stages,
        rule=stage_capacity_rule,
    )

    def minimum_production_rule(instance, product):
        return (
            instance.production[product]
            >= instance.min_production[product]
        )

    model.minimum_production_requirement = pyo.Constraint(
        model.products,
        rule=minimum_production_rule,
    )

    def demand_limit_rule(instance, product):
        return (
            instance.production[product]
            <= instance.max_demand[product]
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
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}