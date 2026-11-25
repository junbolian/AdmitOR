# IR: {"sets":{"products":"0..5","stages":"0..10"},"params":{"profit":"real[products]","stage_capacity":"real[stages]","min_commitment":"real[products]","market_demand":"real[products]","stage_time":"real[stages,products]"},"variables":{"production":"nonnegative continuous[products]"},"constraints":["forall s: sum(stage_time[s,p]*production[p] for p in products) <= stage_capacity[s]","forall p: production[p] >= min_commitment[p]","forall p: production[p] <= market_demand[p]"],"objective":"maximize sum(profit[p]*production[p] for p in products)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.products = pyo.RangeSet(0, 5)
    model.stages = pyo.RangeSet(0, 10)

    model.profit = pyo.Param(
        model.products,
        initialize=lambda mdl, product: params["profit"][product],
        within=pyo.Reals,
    )
    model.stage_capacity = pyo.Param(
        model.stages,
        initialize=lambda mdl, stage: params["stage_capacity"][stage],
        within=pyo.Reals,
    )
    model.min_commitment = pyo.Param(
        model.products,
        initialize=lambda mdl, product: params["min_commitment"][product],
        within=pyo.Reals,
    )
    model.market_demand = pyo.Param(
        model.products,
        initialize=lambda mdl, product: params["market_demand"][product],
        within=pyo.Reals,
    )
    model.stage_time = pyo.Param(
        model.stages,
        model.products,
        initialize=lambda mdl, stage, product: params["stage_time"][stage][product],
        within=pyo.Reals,
    )

    model.production = pyo.Var(model.products, domain=pyo.NonNegativeReals)

    def stage_capacity_rule(mdl, stage):
        return (
            sum(
                mdl.stage_time[stage, product] * mdl.production[product]
                for product in mdl.products
            )
            <= mdl.stage_capacity[stage]
        )

    model.stage_limits = pyo.Constraint(
        model.stages, rule=stage_capacity_rule
    )
    model.minimum_production = pyo.Constraint(
        model.products,
        rule=lambda mdl, product: (
            mdl.production[product] >= mdl.min_commitment[product]
        ),
    )
    model.demand_limits = pyo.Constraint(
        model.products,
        rule=lambda mdl, product: (
            mdl.production[product] <= mdl.market_demand[product]
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
    except RuntimeError as exc:
        if "A feasible solution was not found" in str(exc):
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_profit))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}