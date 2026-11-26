# IR: {"sets":{"T":["high","mid","low"]},"params":{"profit[t]":["profit_high","profit_mid","profit_low"],"labor[t]":["labor_high","labor_mid","labor_low"],"inspect[t]":["inspect_high","inspect_mid","inspect_low"],"demand[t]":["demand_high","demand_mid","demand_low"],"labor_capacity":"labor_capacity","inspection_capacity":"inspection_capacity"},"variables":{"production[t]":"nonnegative integer"},"constraints":["sum(labor[t]*production[t] for t in T) <= labor_capacity","sum(inspect[t]*production[t] for t in T) <= inspection_capacity","production[t] <= demand[t] for each t in T"],"objective":"maximize sum(profit[t]*production[t] for t in T)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.toy_types = pyo.Set(
        initialize=["high", "mid", "low"],
        ordered=True,
    )

    model.unit_profit = pyo.Param(
        model.toy_types,
        initialize={
            "high": params["profit_high"],
            "mid": params["profit_mid"],
            "low": params["profit_low"],
        },
    )
    model.labor_hours = pyo.Param(
        model.toy_types,
        initialize={
            "high": params["labor_high"],
            "mid": params["labor_mid"],
            "low": params["labor_low"],
        },
    )
    model.inspection_hours = pyo.Param(
        model.toy_types,
        initialize={
            "high": params["inspect_high"],
            "mid": params["inspect_mid"],
            "low": params["inspect_low"],
        },
    )
    model.market_demand = pyo.Param(
        model.toy_types,
        initialize={
            "high": params["demand_high"],
            "mid": params["demand_mid"],
            "low": params["demand_low"],
        },
    )
    model.available_labor = pyo.Param(
        initialize=params["labor_capacity"],
    )
    model.available_inspection = pyo.Param(
        initialize=params["inspection_capacity"],
    )

    model.production = pyo.Var(
        model.toy_types,
        domain=pyo.NonNegativeIntegers,
    )

    model.labor_limit = pyo.Constraint(
        expr=sum(
            model.labor_hours[toy] * model.production[toy]
            for toy in model.toy_types
        )
        <= model.available_labor
    )
    model.inspection_limit = pyo.Constraint(
        expr=sum(
            model.inspection_hours[toy] * model.production[toy]
            for toy in model.toy_types
        )
        <= model.available_inspection
    )

    def demand_limit_rule(mdl, toy):
        return mdl.production[toy] <= mdl.market_demand[toy]

    model.demand_limit = pyo.Constraint(
        model.toy_types,
        rule=demand_limit_rule,
    )

    model.total_profit = pyo.Objective(
        expr=sum(
            model.unit_profit[toy] * model.production[toy]
            for toy in model.toy_types
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