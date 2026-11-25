# IR: {"sets":{"types":[0,1],"periods":[0,1,2,3]},"params":["base_cost_type0","base_cost_type1","var_cost_type0","var_cost_type1","startup_cost_type0","startup_cost_type1","max_units_type0","max_units_type1","demand","min_output_type0","max_output_type0","min_output_type1","max_output_type1","reserve_margin","max_startup_type0_period0","max_startup_type1_period0"],"variables":{"units[k,t]":"nonnegative integer, <= max_units[k]","output[k,t]":"nonnegative continuous","startups[k,t]":"nonnegative integer"},"constraints":["output[k,t] >= min_output[k]*units[k,t]","output[k,t] <= max_output[k]*units[k,t]","sum_k output[k,t] >= demand[t]","sum_k max_output[k]*units[k,t] >= (1+reserve_margin)*demand[t]","startups[k,0] = units[k,0] (initially all units are off)","startups[k,0] <= initial_startup_limit[k]","startups[k,t] >= units[k,t]-units[k,t-1] for t>0","startups[k,t] <= units[k,t-1] for t>0 (literal previous-period startup limit)"],"objective":"minimize sum_{k,t}(base_cost[k]*units[k,t]+var_cost[k]*output[k,t]+startup_cost[k]*startups[k,t])"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.generator_types = pyo.Set(initialize=[0, 1], ordered=True)
    model.periods = pyo.RangeSet(0, 3)
    model.later_periods = pyo.RangeSet(1, 3)

    model.base_cost = pyo.Param(
        model.generator_types,
        initialize={
            0: params["base_cost_type0"],
            1: params["base_cost_type1"],
        },
        within=pyo.Reals,
    )
    model.variable_cost = pyo.Param(
        model.generator_types,
        initialize={
            0: params["var_cost_type0"],
            1: params["var_cost_type1"],
        },
        within=pyo.Reals,
    )
    model.startup_cost = pyo.Param(
        model.generator_types,
        initialize={
            0: params["startup_cost_type0"],
            1: params["startup_cost_type1"],
        },
        within=pyo.Reals,
    )
    model.unit_limit = pyo.Param(
        model.generator_types,
        initialize={
            0: params["max_units_type0"],
            1: params["max_units_type1"],
        },
        within=pyo.NonNegativeIntegers,
    )
    model.minimum_output = pyo.Param(
        model.generator_types,
        initialize={
            0: params["min_output_type0"],
            1: params["min_output_type1"],
        },
        within=pyo.NonNegativeReals,
    )
    model.maximum_output = pyo.Param(
        model.generator_types,
        initialize={
            0: params["max_output_type0"],
            1: params["max_output_type1"],
        },
        within=pyo.NonNegativeReals,
    )
    model.power_demand = pyo.Param(
        model.periods,
        initialize={period: params["demand"][period] for period in range(4)},
        within=pyo.NonNegativeReals,
    )
    model.reserve_fraction = pyo.Param(
        initialize=params["reserve_margin"],
        within=pyo.NonNegativeReals,
    )
    model.initial_startup_limit = pyo.Param(
        model.generator_types,
        initialize={
            0: params["max_startup_type0_period0"],
            1: params["max_startup_type1_period0"],
        },
        within=pyo.NonNegativeIntegers,
    )

    def unit_bounds(instance, generator_type, period):
        return 0, instance.unit_limit[generator_type]

    model.units = pyo.Var(
        model.generator_types,
        model.periods,
        domain=pyo.NonNegativeIntegers,
        bounds=unit_bounds,
    )
    model.output = pyo.Var(
        model.generator_types,
        model.periods,
        domain=pyo.NonNegativeReals,
    )
    model.startups = pyo.Var(
        model.generator_types,
        model.periods,
        domain=pyo.NonNegativeIntegers,
    )

    def minimum_generation_rule(instance, generator_type, period):
        return (
            instance.output[generator_type, period]
            >= instance.minimum_output[generator_type]
            * instance.units[generator_type, period]
        )

    model.minimum_generation = pyo.Constraint(
        model.generator_types,
        model.periods,
        rule=minimum_generation_rule,
    )

    def maximum_generation_rule(instance, generator_type, period):
        return (
            instance.output[generator_type, period]
            <= instance.maximum_output[generator_type]
            * instance.units[generator_type, period]
        )

    model.maximum_generation = pyo.Constraint(
        model.generator_types,
        model.periods,
        rule=maximum_generation_rule,
    )

    def demand_rule(instance, period):
        return (
            sum(
                instance.output[generator_type, period]
                for generator_type in instance.generator_types
            )
            >= instance.power_demand[period]
        )

    model.demand_requirement = pyo.Constraint(model.periods, rule=demand_rule)

    def reserve_rule(instance, period):
        return (
            sum(
                instance.maximum_output[generator_type]
                * instance.units[generator_type, period]
                for generator_type in instance.generator_types
            )
            >= (1 + instance.reserve_fraction) * instance.power_demand[period]
        )

    model.reserve_requirement = pyo.Constraint(model.periods, rule=reserve_rule)

    def initial_startup_balance_rule(instance, generator_type):
        return (
            instance.startups[generator_type, 0]
            == instance.units[generator_type, 0]
        )

    model.initial_startup_balance = pyo.Constraint(
        model.generator_types,
        rule=initial_startup_balance_rule,
    )

    def initial_startup_cap_rule(instance, generator_type):
        return (
            instance.startups[generator_type, 0]
            <= instance.initial_startup_limit[generator_type]
        )

    model.initial_startup_cap = pyo.Constraint(
        model.generator_types,
        rule=initial_startup_cap_rule,
    )

    def startup_requirement_rule(instance, generator_type, period):
        return (
            instance.startups[generator_type, period]
            >= instance.units[generator_type, period]
            - instance.units[generator_type, period - 1]
        )

    model.startup_requirement = pyo.Constraint(
        model.generator_types,
        model.later_periods,
        rule=startup_requirement_rule,
    )

    def subsequent_startup_cap_rule(instance, generator_type, period):
        return (
            instance.startups[generator_type, period]
            <= instance.units[generator_type, period - 1]
        )

    model.subsequent_startup_cap = pyo.Constraint(
        model.generator_types,
        model.later_periods,
        rule=subsequent_startup_cap_rule,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.base_cost[generator_type] * model.units[generator_type, period]
            + model.variable_cost[generator_type]
            * model.output[generator_type, period]
            + model.startup_cost[generator_type]
            * model.startups[generator_type, period]
            for generator_type in model.generator_types
            for period in model.periods
        ),
        sense=pyo.minimize,
    )

    objective_failure_status = "objective_unavailable"
    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPSI raises this specific error when no feasible solution can be
        # loaded. Unexpected runtime errors are allowed to propagate.
        if "A feasible solution was not found" not in str(exc):
            raise
        objective_failure_status = "no_feasible_solution"

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": objective_failure_status}

    return {"objective": obj_val, "status": "optimal"}