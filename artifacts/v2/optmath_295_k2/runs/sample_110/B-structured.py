# IR: {"sets":{"K":[0,1],"T":[0,1,2,3,4],"T_later":[1,2,3,4]},"params":["base_cost_type0","base_cost_type1","power_cost_type0","power_cost_type1","startup_cost_type0","startup_cost_type1","demand","min_output_type0","max_output_type0","min_output_type1","max_output_type1","reserve_margin","max_active_per_type","max_startups_first_type0","max_startups_first_type1"],"variables":{"active_units[K,T]":"nonnegative integer","startups[K,T]":"nonnegative integer","output[K,T]":"nonnegative continuous; aggregate MW by type"},"constraints":["active_units[k,t] <= max_active_per_type","output[k,t] >= min_output[k]*active_units[k,t]","output[k,t] <= max_output[k]*active_units[k,t]","sum_k output[k,t] >= demand[t]","sum_k max_output[k]*active_units[k,t] >= (1+reserve_margin)*demand[t]","active_units[k,0] <= startups[k,0] (initially off)","startups[k,0] <= max_startups_first[k]","active_units[k,t] <= active_units[k,t-1]+startups[k,t] for t>0","startups[k,t] <= active_units[k,t]-active_units[k,t-1] for t>0"],"objective":"minimize sum_{k,t}(base_cost[k]*active_units[k,t]+power_cost[k]*output[k,t]+startup_cost[k]*startups[k,t])"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.generator_types = pyo.Set(initialize=[0, 1], ordered=True)
    model.periods = pyo.RangeSet(0, 4)
    model.later_periods = pyo.RangeSet(1, 4)

    model.base_cost = pyo.Param(
        model.generator_types,
        initialize={
            0: params["base_cost_type0"],
            1: params["base_cost_type1"],
        },
    )
    model.power_cost = pyo.Param(
        model.generator_types,
        initialize={
            0: params["power_cost_type0"],
            1: params["power_cost_type1"],
        },
    )
    model.startup_cost = pyo.Param(
        model.generator_types,
        initialize={
            0: params["startup_cost_type0"],
            1: params["startup_cost_type1"],
        },
    )
    model.demand = pyo.Param(
        model.periods,
        initialize={period: params["demand"][period] for period in range(5)},
    )
    model.min_output = pyo.Param(
        model.generator_types,
        initialize={
            0: params["min_output_type0"],
            1: params["min_output_type1"],
        },
    )
    model.max_output = pyo.Param(
        model.generator_types,
        initialize={
            0: params["max_output_type0"],
            1: params["max_output_type1"],
        },
    )
    model.reserve_margin = pyo.Param(initialize=params["reserve_margin"])
    model.max_active_per_type = pyo.Param(
        initialize=params["max_active_per_type"]
    )
    model.max_startups_first = pyo.Param(
        model.generator_types,
        initialize={
            0: params["max_startups_first_type0"],
            1: params["max_startups_first_type1"],
        },
    )

    # "active" is a reserved Pyomo attribute; use "active_units".
    model.active_units = pyo.Var(
        model.generator_types, model.periods, domain=pyo.NonNegativeIntegers
    )
    model.startups = pyo.Var(
        model.generator_types, model.periods, domain=pyo.NonNegativeIntegers
    )
    model.output = pyo.Var(
        model.generator_types, model.periods, domain=pyo.NonNegativeReals
    )

    model.active_limit = pyo.Constraint(
        model.generator_types,
        model.periods,
        rule=lambda mdl, kind, period: (
            mdl.active_units[kind, period] <= mdl.max_active_per_type
        ),
    )
    model.minimum_generation = pyo.Constraint(
        model.generator_types,
        model.periods,
        rule=lambda mdl, kind, period: (
            mdl.output[kind, period]
            >= mdl.min_output[kind] * mdl.active_units[kind, period]
        ),
    )
    model.maximum_generation = pyo.Constraint(
        model.generator_types,
        model.periods,
        rule=lambda mdl, kind, period: (
            mdl.output[kind, period]
            <= mdl.max_output[kind] * mdl.active_units[kind, period]
        ),
    )
    model.demand_requirement = pyo.Constraint(
        model.periods,
        rule=lambda mdl, period: (
            sum(mdl.output[kind, period] for kind in mdl.generator_types)
            >= mdl.demand[period]
        ),
    )
    model.reserve_requirement = pyo.Constraint(
        model.periods,
        rule=lambda mdl, period: (
            sum(
                mdl.max_output[kind] * mdl.active_units[kind, period]
                for kind in mdl.generator_types
            )
            >= (1 + mdl.reserve_margin) * mdl.demand[period]
        ),
    )
    model.initial_availability = pyo.Constraint(
        model.generator_types,
        rule=lambda mdl, kind: (
            mdl.active_units[kind, 0] <= mdl.startups[kind, 0]
        ),
    )
    model.initial_startup_limit = pyo.Constraint(
        model.generator_types,
        rule=lambda mdl, kind: (
            mdl.startups[kind, 0] <= mdl.max_startups_first[kind]
        ),
    )
    model.period_availability = pyo.Constraint(
        model.generator_types,
        model.later_periods,
        rule=lambda mdl, kind, period: (
            mdl.active_units[kind, period]
            <= mdl.active_units[kind, period - 1] + mdl.startups[kind, period]
        ),
    )

    # Enforce the stated upper bound literally. Combined with availability,
    # it equates startups to the increase and prevents active counts decreasing.
    model.startup_increase_limit = pyo.Constraint(
        model.generator_types,
        model.later_periods,
        rule=lambda mdl, kind, period: (
            mdl.startups[kind, period]
            <= mdl.active_units[kind, period]
            - mdl.active_units[kind, period - 1]
        ),
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.base_cost[kind] * model.active_units[kind, period]
            + model.power_cost[kind] * model.output[kind, period]
            + model.startup_cost[kind] * model.startups[kind, period]
            for kind in model.generator_types
            for period in model.periods
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as error:
        if "a feasible solution was not found" not in str(error).lower():
            raise
        # Continue to objective retrieval as the sole success test.

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}