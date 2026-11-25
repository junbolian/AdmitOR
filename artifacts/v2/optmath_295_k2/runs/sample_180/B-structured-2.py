# IR: {"sets":{"products":"0..5","stages":"0..10"},"params":{"profit":"real[products]","stage_capacity":"real[stages]","min_commitment":"real[products]","market_demand":"real[products]","stage_time":"real[stages,products]"},"variables":{"production":"continuous nonnegative[products]"},"constraints":["sum(stage_time[s,p]*production[p] for p in products) <= stage_capacity[s] for s in stages","production[p] >= min_commitment[p] for p in products","production[p] <= market_demand[p] for p in products"],"objective":"maximize sum(profit[p]*production[p] for p in products)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.products = pyo.RangeSet(0, 5)
    model.stages = pyo.RangeSet(0, 10)

    model.profit = pyo.Param(
        model.products,
        initialize={
            product: params["profit"][product]
            for product in model.products
        },
        within=pyo.Reals,
    )
    model.stage_capacity = pyo.Param(
        model.stages,
        initialize={
            stage: params["stage_capacity"][stage]
            for stage in model.stages
        },
        within=pyo.Reals,
    )
    model.min_commitment = pyo.Param(
        model.products,
        initialize={
            product: params["min_commitment"][product]
            for product in model.products
        },
        within=pyo.Reals,
    )
    model.market_demand = pyo.Param(
        model.products,
        initialize={
            product: params["market_demand"][product]
            for product in model.products
        },
        within=pyo.Reals,
    )
    model.stage_time = pyo.Param(
        model.stages,
        model.products,
        initialize={
            (stage, product): params["stage_time"][stage][product]
            for stage in model.stages
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
            instance.stage_time[stage, product]
            * instance.production[product]
            for product in instance.products
        ) <= instance.stage_capacity[stage]

    model.stage_capacity_constraints = pyo.Constraint(
        model.stages,
        rule=stage_capacity_rule,
    )

    def minimum_commitment_rule(instance, product):
        return (
            instance.production[product]
            >= instance.min_commitment[product]
        )

    model.minimum_commitment_constraints = pyo.Constraint(
        model.products,
        rule=minimum_commitment_rule,
    )

    def market_demand_rule(instance, product):
        return (
            instance.production[product]
            <= instance.market_demand[product]
        )

    model.market_demand_constraints = pyo.Constraint(
        model.products,
        rule=market_demand_rule,
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