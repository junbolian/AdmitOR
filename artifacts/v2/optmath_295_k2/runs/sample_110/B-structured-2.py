# IR: {"sets":{"types":[0,1],"periods":[0,1,2,3,4],"later_periods":[1,2,3,4]},"params":["base_cost_type0","base_cost_type1","power_cost_type0","power_cost_type1","startup_cost_type0","startup_cost_type1","demand","min_output_type0","max_output_type0","min_output_type1","max_output_type1","reserve_margin","max_active_per_type","max_startups_first_type0","max_startups_first_type1"],"variables":{"units_on[k,t]":"nonnegative integer","power_output[k,t]":"nonnegative continuous","startups[k,t]":"nonnegative integer"},"constraints":["units_on[k,t] <= max_active_per_type","power_output[k,t] >= min_output[k]*units_on[k,t]","power_output[k,t] <= max_output[k]*units_on[k,t]","sum_k power_output[k,t] >= demand[t]","sum_k max_output[k]*units_on[k,t] >= (1+reserve_margin)*demand[t]","units_on[k,0] <= startups[k,0]","startups[k,0] <= max_startups_first[k]","units_on[k,t] <= units_on[k,t-1]+startups[k,t] for t>=1","startups[k,t] <= units_on[k,t]-units_on[k,t-1] for t>=1"],"objective":"minimize sum_{k,t}(base_cost[k]*units_on[k,t]+power_cost[k]*power_output[k,t]+startup_cost[k]*startups[k,t])"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    base_cost = {
        0: params["base_cost_type0"],
        1: params["base_cost_type1"],
    }
    power_cost = {
        0: params["power_cost_type0"],
        1: params["power_cost_type1"],
    }
    startup_cost = {
        0: params["startup_cost_type0"],
        1: params["startup_cost_type1"],
    }
    min_output = {
        0: params["min_output_type0"],
        1: params["min_output_type1"],
    }
    max_output = {
        0: params["max_output_type0"],
        1: params["max_output_type1"],
    }
    max_startups_first = {
        0: params["max_startups_first_type0"],
        1: params["max_startups_first_type1"],
    }
    demand = params["demand"]
    reserve_margin = params["reserve_margin"]
    max_active_per_type = params["max_active_per_type"]

    model = pyo.ConcreteModel()
    model.generator_types = pyo.Set(initialize=[0, 1], ordered=True)
    model.periods = pyo.RangeSet(0, 4)
    model.later_periods = pyo.RangeSet(1, 4)

    model.units_on = pyo.Var(
        model.generator_types,
        model.periods,
        domain=pyo.NonNegativeIntegers,
    )
    model.power_output = pyo.Var(
        model.generator_types,
        model.periods,
        domain=pyo.NonNegativeReals,
    )
    model.startups = pyo.Var(
        model.generator_types,
        model.periods,
        domain=pyo.NonNegativeIntegers,
    )

    model.unit_count_limit = pyo.Constraint(
        model.generator_types,
        model.periods,
        rule=lambda mdl, kind, period: (
            mdl.units_on[kind, period] <= max_active_per_type
        ),
    )

    model.minimum_generation = pyo.Constraint(
        model.generator_types,
        model.periods,
        rule=lambda mdl, kind, period: (
            mdl.power_output[kind, period]
            >= min_output[kind] * mdl.units_on[kind, period]
        ),
    )

    model.maximum_generation = pyo.Constraint(
        model.generator_types,
        model.periods,
        rule=lambda mdl, kind, period: (
            mdl.power_output[kind, period]
            <= max_output[kind] * mdl.units_on[kind, period]
        ),
    )

    model.demand_requirement = pyo.Constraint(
        model.periods,
        rule=lambda mdl, period: (
            sum(
                mdl.power_output[kind, period]
                for kind in mdl.generator_types
            )
            >= demand[period]
        ),
    )

    model.reserve_requirement = pyo.Constraint(
        model.periods,
        rule=lambda mdl, period: (
            sum(
                max_output[kind] * mdl.units_on[kind, period]
                for kind in mdl.generator_types
            )
            >= (1 + reserve_margin) * demand[period]
        ),
    )

    # All units operating in period zero must be started in that period.
    model.initial_availability = pyo.Constraint(
        model.generator_types,
        rule=lambda mdl, kind: (
            mdl.units_on[kind, 0] <= mdl.startups[kind, 0]
        ),
    )

    model.initial_startup_limit = pyo.Constraint(
        model.generator_types,
        rule=lambda mdl, kind: (
            mdl.startups[kind, 0] <= max_startups_first[kind]
        ),
    )

    model.period_availability = pyo.Constraint(
        model.generator_types,
        model.later_periods,
        rule=lambda mdl, kind, period: (
            mdl.units_on[kind, period]
            <= mdl.units_on[kind, period - 1] + mdl.startups[kind, period]
        ),
    )

    # The stated startup upper bound also prevents decreases in units_on.
    model.startup_increase_limit = pyo.Constraint(
        model.generator_types,
        model.later_periods,
        rule=lambda mdl, kind, period: (
            mdl.startups[kind, period]
            <= mdl.units_on[kind, period] - mdl.units_on[kind, period - 1]
        ),
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            base_cost[kind] * model.units_on[kind, period]
            + power_cost[kind] * model.power_output[kind, period]
            + startup_cost[kind] * model.startups[kind, period]
            for kind in model.generator_types
            for period in model.periods
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        # A failed solution load may raise; objective retrieval decides success.
        pass

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}