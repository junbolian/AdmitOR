# {"sets":{"products":"0..5","stages":"0..10"},"params":{"profit":"products -> real","stage_capacity":"stages -> real","time_coeff":"stages x products -> real","min_production":"products -> real","market_demand":"products -> real"},"variables":{"quantity":"products -> nonnegative continuous"},"constraints":["For each stage s: sum(time_coeff[s,p]*quantity[p] for p in products) <= stage_capacity[s]","For each product p: quantity[p] >= min_production[p]","For each product p: quantity[p] <= market_demand[p]"],"objective":"maximize sum(profit[p]*quantity[p] for p in products)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    profit = params["profit"]
    stage_capacity = params["stage_capacity"]
    time_coeff = params["time_coeff"]
    min_production = params["min_production"]
    market_demand = params["market_demand"]

    model = pyo.ConcreteModel()
    model.products = pyo.RangeSet(0, 5)
    model.stages = pyo.RangeSet(0, 10)

    model.profit = pyo.Param(
        model.products,
        initialize={p: profit[p] for p in model.products},
    )
    model.stage_capacity = pyo.Param(
        model.stages,
        initialize={s: stage_capacity[s] for s in model.stages},
    )
    model.time_coeff = pyo.Param(
        model.stages,
        model.products,
        initialize={
            (s, p): time_coeff[s][p]
            for s in model.stages
            for p in model.products
        },
    )
    model.min_production = pyo.Param(
        model.products,
        initialize={p: min_production[p] for p in model.products},
    )
    model.market_demand = pyo.Param(
        model.products,
        initialize={p: market_demand[p] for p in model.products},
    )

    model.quantity = pyo.Var(model.products, domain=pyo.NonNegativeReals)

    def capacity_rule(instance, s):
        return (
            sum(
                instance.time_coeff[s, p] * instance.quantity[p]
                for p in instance.products
            )
            <= instance.stage_capacity[s]
        )

    def minimum_rule(instance, p):
        return instance.quantity[p] >= instance.min_production[p]

    def demand_rule(instance, p):
        return instance.quantity[p] <= instance.market_demand[p]

    model.capacity_limits = pyo.Constraint(model.stages, rule=capacity_rule)
    model.minimum_commitments = pyo.Constraint(model.products, rule=minimum_rule)
    model.demand_limits = pyo.Constraint(model.products, rule=demand_rule)

    model.total_profit = pyo.Objective(
        expr=sum(
            model.profit[p] * model.quantity[p] for p in model.products
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