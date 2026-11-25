# IR: {"sets":{"products":"0..5","stages":"0..10"},"params":{"profit":"profit[product]","avail":"avail[stage]","time":"time[stage][product], stage-major","minProd":"minProd[product]","maxProd":"maxProd[product]"},"variables":{"production[product]":"NonNegativeReals"},"constraints":["For each stage: sum(time[stage][product] * production[product] for product) <= avail[stage]","For each product: production[product] >= minProd[product]","For each product: production[product] <= maxProd[product]"],"objective":"maximize sum(profit[product] * production[product] for product)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.products = pyo.RangeSet(0, 5)
    model.stages = pyo.RangeSet(0, 10)

    model.unit_profit = pyo.Param(
        model.products,
        initialize=lambda mdl, product: params["profit"][product],
    )
    model.available_time = pyo.Param(
        model.stages,
        initialize=lambda mdl, stage: params["avail"][stage],
    )
    model.processing_time = pyo.Param(
        model.stages,
        model.products,
        initialize=lambda mdl, stage, product: params["time"][stage][product],
    )
    model.minimum_production = pyo.Param(
        model.products,
        initialize=lambda mdl, product: params["minProd"][product],
    )
    model.maximum_production = pyo.Param(
        model.products,
        initialize=lambda mdl, product: params["maxProd"][product],
    )

    model.production = pyo.Var(
        model.products,
        domain=pyo.NonNegativeReals,
    )

    def stage_capacity_rule(mdl, stage):
        return (
            sum(
                mdl.processing_time[stage, product] * mdl.production[product]
                for product in mdl.products
            )
            <= mdl.available_time[stage]
        )

    model.stage_capacity = pyo.Constraint(
        model.stages,
        rule=stage_capacity_rule,
    )

    model.minimum_commitment = pyo.Constraint(
        model.products,
        rule=lambda mdl, product: (
            mdl.production[product] >= mdl.minimum_production[product]
        ),
    )

    model.market_demand = pyo.Constraint(
        model.products,
        rule=lambda mdl, product: (
            mdl.production[product] <= mdl.maximum_production[product]
        ),
    )

    model.total_profit = pyo.Objective(
        expr=sum(
            model.unit_profit[product] * model.production[product]
            for product in model.products
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_profit))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}