# IR: {"sets":{"products":"0..5","stages":"0..10"},"params":{"profit":"real[products]","stage_capacity":"real[stages]","stage_time":"real[stages,products], row-major","min_production":"real[products]","max_demand":"real[products]"},"variables":{"production":"nonnegative continuous[products]"},"constraints":["sum(stage_time[s,p]*production[p] for p in products) <= stage_capacity[s], for each stage s","production[p] >= min_production[p], for each product p","production[p] <= max_demand[p], for each product p"],"objective":"maximize sum(profit[p]*production[p] for p in products)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.products = pyo.RangeSet(0, 5)
    model.stages = pyo.RangeSet(0, 10)

    profit = params["profit"]
    stage_capacity = params["stage_capacity"]
    stage_time = params["stage_time"]
    min_production = params["min_production"]
    max_demand = params["max_demand"]

    # Accept either an 11-by-6 nested array or a flat row-major array.
    flat_stage_time = len(stage_time) == 11 * 6

    model.profit = pyo.Param(
        model.products,
        initialize=lambda mdl, product: profit[product],
        within=pyo.Reals,
    )
    model.stage_capacity = pyo.Param(
        model.stages,
        initialize=lambda mdl, stage: stage_capacity[stage],
        within=pyo.Reals,
    )
    model.stage_time = pyo.Param(
        model.stages,
        model.products,
        initialize=lambda mdl, stage, product: (
            stage_time[stage * 6 + product]
            if flat_stage_time
            else stage_time[stage][product]
        ),
        within=pyo.Reals,
    )
    model.min_production = pyo.Param(
        model.products,
        initialize=lambda mdl, product: min_production[product],
        within=pyo.Reals,
    )
    model.max_demand = pyo.Param(
        model.products,
        initialize=lambda mdl, product: max_demand[product],
        within=pyo.Reals,
    )

    model.production = pyo.Var(
        model.products,
        domain=pyo.NonNegativeReals,
    )

    def stage_limit_rule(mdl, stage):
        return sum(
            mdl.stage_time[stage, product] * mdl.production[product]
            for product in mdl.products
        ) <= mdl.stage_capacity[stage]

    model.stage_limits = pyo.Constraint(
        model.stages,
        rule=stage_limit_rule,
    )

    model.minimum_commitments = pyo.Constraint(
        model.products,
        rule=lambda mdl, product: (
            mdl.production[product] >= mdl.min_production[product]
        ),
    )

    model.demand_limits = pyo.Constraint(
        model.products,
        rule=lambda mdl, product: (
            mdl.production[product] <= mdl.max_demand[product]
        ),
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
        # HiGHS can raise when no feasible solution is available to load.
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_profit))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}