# IR: {"sets":{"products":"0..5","stages":"0..10"},"params":{"profit":"real[products]","stage_time_capacity":"real[stages]","stage_time_coeff":"real[stages,products]","min_commitment":"real[products]","market_demand":"real[products]"},"variables":{"quantity":"nonnegative continuous[products]"},"constraints":["sum(stage_time_coeff[s,p]*quantity[p] for p in products) <= stage_time_capacity[s] for each s in stages","quantity[p] >= min_commitment[p] for each p in products","quantity[p] <= market_demand[p] for each p in products"],"objective":"maximize sum(profit[p]*quantity[p] for p in products)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.products = pyo.RangeSet(0, 5)
    model.stages = pyo.RangeSet(0, 10)

    model.profit = pyo.Param(
        model.products,
        initialize={p: params["profit"][p] for p in model.products},
        within=pyo.Reals,
    )
    model.stage_time_capacity = pyo.Param(
        model.stages,
        initialize={
            s: params["stage_time_capacity"][s] for s in model.stages
        },
        within=pyo.Reals,
    )
    model.stage_time_coeff = pyo.Param(
        model.stages,
        model.products,
        initialize={
            (s, p): params["stage_time_coeff"][s][p]
            for s in model.stages
            for p in model.products
        },
        within=pyo.Reals,
    )
    model.min_commitment = pyo.Param(
        model.products,
        initialize={
            p: params["min_commitment"][p] for p in model.products
        },
        within=pyo.Reals,
    )
    model.market_demand = pyo.Param(
        model.products,
        initialize={
            p: params["market_demand"][p] for p in model.products
        },
        within=pyo.Reals,
    )

    model.quantity = pyo.Var(
        model.products,
        domain=pyo.NonNegativeReals,
    )

    def stage_capacity_rule(instance, s):
        return sum(
            instance.stage_time_coeff[s, p] * instance.quantity[p]
            for p in instance.products
        ) <= instance.stage_time_capacity[s]

    model.stage_capacity_constraints = pyo.Constraint(
        model.stages,
        rule=stage_capacity_rule,
    )

    def minimum_commitment_rule(instance, p):
        return instance.quantity[p] >= instance.min_commitment[p]

    model.minimum_commitment_constraints = pyo.Constraint(
        model.products,
        rule=minimum_commitment_rule,
    )

    def market_demand_rule(instance, p):
        return instance.quantity[p] <= instance.market_demand[p]

    model.market_demand_constraints = pyo.Constraint(
        model.products,
        rule=market_demand_rule,
    )

    model.total_profit = pyo.Objective(
        expr=sum(
            model.profit[p] * model.quantity[p]
            for p in model.products
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